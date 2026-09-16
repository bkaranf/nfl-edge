from datetime import UTC, datetime, timedelta
import pytest

from backend.domain import Pick, QuoteInput, Settings, american_to_decimal, game, iso, team_code
from backend.engine import estimate, evaluate, pairs, stake_cap
from backend.providers import quote

NOW = datetime(2026, 9, 15, 12, tzinfo=UTC)
GAME = game("BUF", "DET", NOW + timedelta(days=2))
SETTINGS = Settings(bankroll="1000").model_dump(mode="json")


def pair(book="Bovada", probability=.5, market="total", line=44.5, kind="direct", observed=None, batch=None):
    timestamp = iso(observed or NOW)
    return [quote(GAME, book.lower(), book, market, s, -line if market=="spread" and s=="away" else line,
                  1/p, timestamp, batch or book+timestamp, kind=kind)
            for s,p in zip(("over","under") if market=="total" else ("home","away"), (probability,1-probability))]


def input_quote(**kwargs):
    return QuoteInput(game_id=GAME["id"], market=kwargs.pop("market","total"), side=kwargs.pop("side","over"),
                      line=kwargs.pop("line",44.5), total_cost=kwargs.pop("total_cost","8"), winning_payout=kwargs.pop("winning_payout","20"),
                      observed_at=kwargs.pop("observed_at",NOW), exchange="Kalshi", fees_confirmed=True, rules_confirmed=True, **kwargs)


def references(**kwargs):
    return sum((pair(book=b,**kwargs) for b in ("Bovada","FanDuel","Circa")),[])


def test_coin_minus_115_is_not_fifteen_percent():
    q=input_quote(total_cost="115",winning_payout="215")
    r=evaluate(q,GAME,references(),SETTINGS,[],NOW)
    assert american_to_decimal(-115)==pytest.approx(215/115)
    assert american_to_decimal(100)==2
    assert r["net"]["roi_pct"]==pytest.approx(-6.52173913)
    assert not r["qualified"]


def test_fees_counted_once_and_cap():
    r=evaluate(input_quote(),GAME,references(),SETTINGS,[],NOW)
    assert r["qualified"]
    assert r["net"]["ev"]==2
    assert r["net"]["roi_pct"]==25
    assert r["net"]["stress_roi_pct"]==pytest.approx(20)
    assert r["net"]["max_cost"]==9.59  # 9.60 would leave zero stressed EV.
    assert r["sizing"]["cap"]==5
    assert not r["within_cap"]


def test_deduplicate_book_and_prefer_current_manual_over_redistributed():
    quotes=pair("DraftKings",kind="manual",observed=NOW-timedelta(seconds=30))+pair("DraftKings",kind="redistributed")+pair("Bovada")
    r=evaluate(input_quote(),GAME,quotes,SETTINGS,[],NOW)
    assert r["probability"]["book_count"]==2
    assert r["probability"]["eligible_count"]==2
    assert not r["qualified"]


def test_no_mixing_incomplete_pairs_or_lines_or_suspended_prices():
    pick=Pick(game_id=GAME["id"],market="spread",side="away",line=3.5)
    qs=pair(market="spread",line=-3.5)
    assert len(pairs(qs,pick,SETTINGS,NOW))==1
    qs[0]["batch"]="another snapshot"
    assert not pairs(qs,pick,SETTINGS,NOW)
    qs=pair(market="spread",line=-3)
    assert not pairs(qs,pick,SETTINGS,NOW)
    qs=pair(market="spread",line=-3.5)
    qs[0]["status"]="suspended"
    assert not pairs(qs,pick,SETTINGS,NOW)


@pytest.mark.parametrize("kind,offset",[("redistributed",0),("direct",-121),("manual",10)])
def test_unknown_stale_or_future_age_never_qualifies(kind,offset):
    r=evaluate(input_quote(),GAME,references(kind=kind,observed=NOW+timedelta(seconds=offset)),SETTINGS,[],NOW)
    assert r["probability"]["eligible_count"]==0
    assert not r["qualified"]


def test_tie_sensitivity_uses_worst_return():
    r=evaluate(input_quote(market="moneyline",side="home",line=None,total_cost="15"),GAME,references(market="moneyline",line=None,probability=.8),SETTINGS,[],NOW)
    assert r["net"]["roi_pct"]==pytest.approx((15.7/15-1)*100)
    assert r["net"]["roi_high_pct"]==pytest.approx((16/15-1)*100)
    post={**GAME,"season_type":"POST"}
    assert evaluate(input_quote(market="moneyline",side="home",line=None,total_cost="15"),post,references(market="moneyline",line=None,probability=.8),SETTINGS,[],NOW)["net"]["roi_pct"]==pytest.approx((16/15-1)*100)


@pytest.mark.parametrize("market,side,line,lower,upper",[("total","over",44,44.5,43.5),("total","under",44,43.5,44.5),("spread","home",-3,-3.5,-2.5)])
def test_integer_push_from_adjacent_lines(market,side,line,lower,upper):
    # probability argument is for home / over.
    p1,p2=(.6,.5) if side=="under" else (.4,.5)
    qs=references(market=market,line=lower,probability=p1)+references(market=market,line=upper,probability=p2)
    q=input_quote(market=market,side=side,line=line,push_return="8")
    r=evaluate(q,GAME,qs,SETTINGS,[],NOW)
    assert r["probability"]["win"]==pytest.approx(.4)
    assert r["probability"]["push"]==pytest.approx(.1)
    assert r["net"]["ev"]==pytest.approx(.8)
    assert r["qualified"]


def test_unknown_push_is_blocked_and_incompatible_adjacent_lines_rejected():
    r=evaluate(input_quote(line=44),GAME,references(line=44),SETTINGS,[],NOW)
    assert r["net"] is None
    assert not r["qualified"]
    qs=references(line=44.5,probability=.6)+references(line=43.5,probability=.4)
    r=evaluate(input_quote(line=44,push_return="8"),GAME,qs,SETTINGS,[],NOW)
    assert r["net"] is None


def test_kickoff_quote_age_rules_and_disagreement_gates():
    q=input_quote()
    for update in ({"rules_confirmed":False},{"fees_confirmed":False},{"exchange":"Unknown"},{"observed_at":NOW-timedelta(minutes=3)}):
        assert not evaluate(q.model_copy(update=update),GAME,references(),SETTINGS,[],NOW)["qualified"]
    assert not evaluate(q,{**GAME,"start_time":iso(NOW)},references(),SETTINGS,[],NOW)["qualified"]
    assert not evaluate(q,GAME,pair("Bovada",.4)+pair("Circa",.6)+pair("FanDuel",.5),SETTINGS,[],NOW)["qualified"]


def test_exposure_is_separate_and_never_negative():
    bets=[{"status":"open","quote":{"total_cost":"8.11","game_id":GAME["id"],"mode":"paper"}}]
    assert stake_cap(SETTINGS,bets,GAME["id"],"paper")["cap"]==1.89
    assert stake_cap(SETTINGS,bets,GAME["id"],"actual")["cap"]==5
    assert stake_cap({**SETTINGS,"bankroll":"0"},bets,GAME["id"],"paper")["cap"] is None


def test_team_aliases():
    assert team_code("New York G")=="NYG"
    assert team_code("JAC")=="JAX"
    with pytest.raises(ValueError): team_code("New York")
