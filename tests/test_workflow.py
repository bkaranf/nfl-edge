import asyncio
from datetime import timedelta
import json

import httpx
from fastapi.testclient import TestClient
import pytest

from backend.app import create_app
from backend.domain import (
    Outcome,
    OutcomeReturnRule,
    ProfileAdmission,
    ReturnRequirement,
    iso,
    utcnow,
)
from backend.engine import evaluate
from backend.providers import fetch_kalshi, parse_bovada, parse_espn, parse_kalshi
from backend.service import Service
from backend.settlement_profiles import build_profile, build_registry
from backend.storage import Store
from tests.test_engine import (
    GAME,
    HALF_TOTAL_PROFILE,
    MONEYLINE_PROFILE,
    NOW,
    SETTINGS,
    input_quote,
    pair,
    profile_ref,
    references,
    registry,
)


def test_persistence_accepted_recalculation_settlement_and_export(tmp_path):
    path=tmp_path/'test.sqlite3'
    app=create_app(path,collect=False)
    store=app.state.store
    now=utcnow()
    game={**GAME,"start_time":iso(now+timedelta(days=2))}
    store.put_games([game])
    store.set_settings(SETTINGS)
    store.put_source('fixture',{'status':'ok'},{'quotes':references(observed=now),'observed_at':iso(now)})
    raw=input_quote(observed_at=now).model_dump(mode='json')
    with TestClient(app) as client:
        assert client.get('/api/health').status_code==200
        assert client.post('/api/evaluate',json={**raw,'winning_payout':'NaN'}).status_code==422
        result=client.post('/api/evaluate',json=raw).json()
        assert result['status']=='RESEARCH_ONLY'
        assert not result['qualified']
        assert 'SETTLEMENT_PROFILE_REQUIRED' in result['reason_codes']
        assert client.post('/api/bets',json={**raw,'mode':'actual'}).status_code==422
        actual=client.post('/api/bets',json={**raw,'mode':'actual','placed_confirmed':True})
        assert actual.status_code==201
        assert actual.json()['quote']['outcome_returns']['loss']=='0'
        assert actual.json()['evaluation']['status']=='RESEARCH_ONLY'
        assert not actual.json()['evaluation']['qualified']
        saved=client.post('/api/bets',json={**raw,'total_cost':'9.50','notes':'=FORMULA()'}).json()
        assert saved['evaluation']['net']['roi_pct']==pytest.approx((10/9.5-1)*100)
        original=json.dumps(saved['evaluation'],sort_keys=True)
        client.put('/api/settings',json={**SETTINGS,'min_roi_pct':10})
        settled=client.post(f"/api/bets/{saved['id']}/settle",json={'returned':'20','result':'win'}).json()
        assert settled['settlement']['pnl']==10.5
        assert json.dumps(settled['evaluation'],sort_keys=True)==original
        corrected=client.post(f"/api/bets/{saved['id']}/settle",json={'returned':'9.50','result':'void'}).json()
        assert corrected['audit'][0]['previous_settlement']['pnl']==10.5
        assert "'=FORMULA()" in client.get('/api/export.csv').text
        assert client.post('/api/evaluate',json=raw,headers={'Origin':'https://evil.example'}).status_code==403
    assert Store(path).bets()[0]['settlement']['pnl']==0


def test_actual_record_survives_known_profile_contradiction(tmp_path, monkeypatch):
    monkeypatch.setattr(
        'backend.settlement_profiles.PROFILE_REGISTRY', registry(HALF_TOTAL_PROFILE)
    )
    app=create_app(tmp_path/'contradiction.sqlite3',collect=False)
    now=utcnow()
    game={**GAME,"start_time":iso(now+timedelta(days=2))}
    app.state.store.put_games([game])
    app.state.store.set_settings(SETTINGS)
    app.state.store.put_source(
        'fixture', {'status':'ok'},
        {'quotes':references(observed=now),'observed_at':iso(now)},
    )
    raw=input_quote(
        observed_at=now,
        losing_return='1.00',
        settlement_profile=profile_ref(HALF_TOTAL_PROFILE),
    ).model_dump(mode='json')
    with TestClient(app) as client:
        response=client.post(
            '/api/bets', json={**raw,'mode':'actual','placed_confirmed':True}
        )
    assert response.status_code==201
    saved=response.json()
    assert saved['quote']['outcome_returns']['loss']=='1.00'
    assert saved['evaluation']['status']=='INSUFFICIENT_DATA'
    assert saved['evaluation']['net'] is None
    assert 'SETTLEMENT_PROFILE_CONTRADICTION' in saved['evaluation']['reason_codes']


def test_manual_reference_validation_and_book_deduplication(tmp_path):
    app=create_app(tmp_path/'test.sqlite3',collect=False)
    now=utcnow()
    app.state.store.put_games([GAME])
    body={'game_id':GAME['id'],'market':'spread','line':-3.5,'book':'fanduel','price_a':-110,'price_b':-110,'observed_at':iso(now),'confirmed':True}
    with TestClient(app) as c:
        assert c.post('/api/references',json=body).status_code==201
        assert c.post('/api/references',json={**body,'confirmed':False}).status_code==422
        assert c.post('/api/references',json={**body,'price_a':0}).status_code==422
    qs=app.state.store.quotes()
    assert {q['line'] for q in qs}=={-3.5,3.5}
    assert {q['book'] for q in qs}=={'FanDuel'}


def test_source_failure_does_not_refresh_old_quotes(tmp_path,monkeypatch):
    store=Store(tmp_path/'test.sqlite3')
    observed=iso(NOW)
    store.put_source('bovada',{'status':'ok'},{'quotes':pair(),'observed_at':observed})
    async def fail(*args): raise ValueError('Fixture source unavailable')
    for name in ('fetch_bovada','fetch_espn','fetch_kalshi'):
        monkeypatch.setattr('backend.service.'+name,fail)
    asyncio.run(Service(store).refresh())
    source=next(s for s in store.sources() if s['id']=='bovada')
    assert source['health']['status']=='error'
    assert source['data']['observed_at']==observed
    assert store.quotes()[0]['observed_at']==observed


def test_kalshi_pagination_and_mapping():
    calls=[]
    def respond(req):
        calls.append(str(req.url))
        return httpx.Response(200,json={'markets':[], 'cursor':'page2' if not req.url.params.get('cursor') else ''})
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as c:
            return await fetch_kalshi(c,NOW)
    assert asyncio.run(run())['raw_markets']==[]
    assert len(calls)==6
    m={'status':'active','ticker':'KXNFLSPREAD-26SEP17DETBUF-DET4','yes_sub_title':'Detroit wins by over 3.5 points',
       'floor_strike':3.5,'yes_ask_dollars':'0.30','no_ask_dollars':'0.72','observed_at':iso(NOW)}
    qs=parse_kalshi([m],[GAME])
    assert [(q['side'],q['line']) for q in qs]==[('away',-3.5),('home',3.5)]
    assert all(q['kind']=='exchange' for q in qs)


def test_bovada_parser_exact_line_and_period():
    event={'type':'GAMEEVENT','live':False,'startTime':int(NOW.timestamp()*1000),'competitors':[{'home':True,'name':'Buffalo Bills'},{'home':False,'name':'Detroit Lions'}],
           'displayGroups':[{'description':'Game Lines','markets':[{'id':'a','status':'O','description':'Point Spread','period':{'description':'Game','live':False},
             'outcomes':[{'status':'O','type':'H','price':{'decimal':'1.909091','handicap':'-3.5'}},{'status':'O','type':'A','price':{'decimal':'1.909091','handicap':'3.5'}}]},
             {'id':'b','status':'O','description':'Total','period':{'description':'First Half'},'outcomes':[]}]}]}
    r=parse_bovada([{'events':[event]}],iso(NOW))
    assert len(r['quotes'])==2
    assert {q['line'] for q in r['quotes']}=={-3.5,3.5}
    assert all(q['main'] for q in r['quotes'])


def test_closing_never_uses_post_kickoff_data(tmp_path):
    store=Store(tmp_path/'test.sqlite3')
    start=utcnow()-timedelta(minutes=1)
    g={**GAME,'start_time':iso(start)}
    store.put_games([g])
    entered=start-timedelta(hours=1)
    q=input_quote(observed_at=entered)
    evaluation=evaluate(q,g,references(observed=entered),SETTINGS,[],entered)
    store.add_bet({'quote':q.model_dump(mode='json'),'game':g,'evaluation':evaluation,'notes':'','audit':[]})
    after=start+timedelta(seconds=1)
    store.put_source('fixture',{'status':'ok'},{'observed_at':iso(after),'quotes':references(observed=after)})
    Service(store).capture_closing()
    closing=store.bets()[0]['closing']
    assert closing['status']=='unavailable'
    assert closing['reason']=='No comparable benchmark captured in the last five minutes before kickoff.'
    assert 'reason_code' not in closing


def test_closing_uses_pinned_postseason_no_tie_profile(tmp_path):
    start=utcnow()-timedelta(seconds=1)
    entered=start-timedelta(seconds=30)
    closing_observed=start-timedelta(seconds=10)
    game={**GAME,'start_time':iso(start),'season_type':'POST'}
    settings={**SETTINGS,'max_age_seconds':120}
    profile=build_profile(
        profile_id='test.synthetic.closing-moneyline-post-no-tie',
        version=1,
        exchange='Kalshi',
        product='synthetic-test-only',
        market='moneyline',
        season_types=('POST',),
        overtime_included=True,
        outcome_rules={
            Outcome.WIN: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED),
            Outcome.TIE_OR_PUSH: OutcomeReturnRule(requirement=ReturnRequirement.FORBIDDEN),
            Outcome.LOSS: OutcomeReturnRule(requirement=ReturnRequirement.REQUIRED, exact='0'),
        },
        evidence_ids=('synthetic:test-only',),
        effective_from=entered-timedelta(days=1),
        admission=ProfileAdmission.ADMITTED,
        admitted_at=entered-timedelta(days=1),
        decision_id='synthetic-test-only',
    )
    entered_quote=input_quote(
        market='moneyline',
        side='home',
        line=None,
        total_cost='70',
        winning_payout='100',
        push_return=None,
        losing_return='0',
        observed_at=entered,
        settlement_profile=profile_ref(profile),
    )
    evaluation=evaluate(
        entered_quote,
        game,
        references(market='moneyline',line=None,probability=.74,observed=entered),
        settings,
        [],
        entered,
        build_registry((profile,)),
    )
    snapshot=evaluation['calculation']['settlement_profile']['resolved']
    assert evaluation['calculation']['settlement_profile']['compatible'] is True
    assert snapshot['profile_id']==profile.profile_id
    assert snapshot['version']==profile.version
    assert snapshot['evidence_ids']==['synthetic:test-only']
    assert snapshot['outcome_rules']['tie_or_push']['requirement']=='FORBIDDEN'
    assert evaluation['net']['scenarios'][0]['expected_return_exact']=='74.00'

    store=Store(tmp_path/'post-no-tie.sqlite3')
    store.put_games([game])
    store.set_settings(settings)
    store.add_bet({
        'quote':entered_quote.model_dump(mode='json'),
        'game':game,
        'evaluation':evaluation,
        'notes':'',
        'audit':[],
    })
    store.put_source(
        'fixture',
        {'status':'ok'},
        {
            'observed_at':iso(closing_observed),
            'quotes':references(
                market='moneyline',line=None,probability=.74,observed=closing_observed
            ),
        },
    )
    Service(store).capture_closing()
    closing=store.bets()[0]['closing']
    assert closing['status']=='supported'
    assert closing['probability']['eligible_count']==3
    assert closing['roi_pct']==pytest.approx((74/70-1)*100)


def test_closing_preserves_explicit_tie_return_and_never_invents_one(tmp_path):
    start=utcnow()-timedelta(seconds=1)
    entered=start-timedelta(seconds=30)
    closing_observed=start-timedelta(seconds=10)
    game={**GAME,'start_time':iso(start),'season_type':'REG'}
    settings={**SETTINGS,'max_age_seconds':120}
    registry_snapshot=build_registry((MONEYLINE_PROFILE,))
    closing_quotes=references(
        market='moneyline',line=None,probability=.74,observed=closing_observed
    )

    explicit_quote=input_quote(
        market='moneyline',
        side='home',
        line=None,
        total_cost='70.60',
        winning_payout='100',
        push_return='0',
        losing_return='0',
        observed_at=entered,
        settlement_profile=profile_ref(MONEYLINE_PROFILE),
    )
    explicit_evaluation=evaluate(
        explicit_quote,
        game,
        references(market='moneyline',line=None,probability=.74,observed=entered),
        settings,
        [],
        entered,
        registry_snapshot,
    )
    settlement=explicit_evaluation['calculation']['settlement_profile']
    assert settlement['compatible'] is True
    assert settlement['resolved']['profile_id']==MONEYLINE_PROFILE.profile_id
    assert settlement['resolved']['outcome_rules']['tie_or_push']['requirement']=='REQUIRED'
    assert len(explicit_evaluation['net']['scenarios'])==2
    assert min(
        scenario['expected_return'] for scenario in explicit_evaluation['net']['scenarios']
    )==pytest.approx(70.30)

    store=Store(tmp_path/'explicit-tie.sqlite3')
    store.put_games([game])
    store.set_settings(settings)
    store.add_bet({
        'quote':explicit_quote.model_dump(mode='json'),
        'game':game,
        'evaluation':explicit_evaluation,
        'notes':'',
        'audit':[],
    })
    store.put_source(
        'fixture',
        {'status':'ok'},
        {'observed_at':iso(closing_observed),'quotes':closing_quotes},
    )
    Service(store).capture_closing()
    closing=store.bets()[0]['closing']
    assert closing['status']=='supported'
    assert closing['roi_pct']==pytest.approx((70.30/70.60-1)*100)

    missing_quote=input_quote(
        market='moneyline',
        side='home',
        line=None,
        total_cost='70.60',
        winning_payout='100',
        push_return=None,
        losing_return='0',
        observed_at=entered,
        settlement_profile=profile_ref(MONEYLINE_PROFILE),
    )
    missing_evaluation=evaluate(
        missing_quote,
        game,
        references(market='moneyline',line=None,probability=.74,observed=entered),
        settings,
        [],
        entered,
        registry_snapshot,
    )
    assert missing_evaluation['net'] is None
    missing_store=Store(tmp_path/'missing-tie.sqlite3')
    missing_store.put_games([game])
    missing_store.set_settings(settings)
    missing_store.add_bet({
        'quote':missing_quote.model_dump(mode='json'),
        'game':game,
        'evaluation':missing_evaluation,
        'notes':'',
        'audit':[],
    })
    missing_store.put_source(
        'fixture',
        {'status':'ok'},
        {'observed_at':iso(closing_observed),'quotes':closing_quotes},
    )
    Service(missing_store).capture_closing()
    missing_closing=missing_store.bets()[0]['closing']
    assert missing_closing['status']=='unavailable'
    assert missing_closing['reason_code']=='OUTCOME_RETURN_REQUIRED'
    assert 'roi_pct' not in missing_closing


def test_closing_blocks_pinned_known_profile_contradiction_and_missing_proof(tmp_path):
    start=utcnow()-timedelta(seconds=1)
    entered=start-timedelta(seconds=30)
    closing_observed=start-timedelta(seconds=10)
    game={**GAME,'start_time':iso(start),'season_type':'REG'}
    settings={**SETTINGS,'max_age_seconds':120}
    entered_quote=input_quote(
        total_cost='8',
        winning_payout='20',
        losing_return='1',
        observed_at=entered,
        settlement_profile=profile_ref(HALF_TOTAL_PROFILE),
    )
    evaluation=evaluate(
        entered_quote,
        game,
        references(probability=.5,observed=entered),
        settings,
        [],
        entered,
        build_registry((HALF_TOTAL_PROFILE,)),
    )
    settlement=evaluation['calculation']['settlement_profile']
    assert settlement['resolved']['profile_id']==HALF_TOTAL_PROFILE.profile_id
    assert settlement['compatible'] is False
    assert evaluation['net'] is None
    assert 'SETTLEMENT_PROFILE_CONTRADICTION' in evaluation['reason_codes']

    def capture(path, pinned_evaluation, quote_input=entered_quote):
        store=Store(path)
        store.put_games([game])
        store.set_settings(settings)
        store.add_bet({
            'quote':quote_input.model_dump(mode='json'),
            'game':game,
            'evaluation':pinned_evaluation,
            'notes':'',
            'audit':[],
        })
        store.put_source(
            'fixture',
            {'status':'ok'},
            {
                'observed_at':iso(closing_observed),
                'quotes':references(probability=.5,observed=closing_observed),
            },
        )
        Service(store).capture_closing()
        return store.bets()[0]['closing']

    contradiction=capture(tmp_path/'closing-contradiction.sqlite3',evaluation)
    assert contradiction['status']=='unavailable'
    assert contradiction['reason_code']=='SETTLEMENT_PROFILE_CONTRADICTION'
    assert 'pinned settlement profile' in contradiction['reason']
    assert 'roi_pct' not in contradiction

    valid_quote=input_quote(
        total_cost='8',
        winning_payout='20',
        losing_return='0',
        observed_at=entered,
        settlement_profile=profile_ref(HALF_TOTAL_PROFILE),
    )
    valid_evaluation=evaluate(
        valid_quote,
        game,
        references(probability=.5,observed=entered),
        settings,
        [],
        entered,
        build_registry((HALF_TOTAL_PROFILE,)),
    )
    valid_settlement=valid_evaluation['calculation']['settlement_profile']
    assert valid_settlement['compatible'] is True
    unproven_settlement={
        key:value for key,value in valid_settlement.items() if key!='compatible'
    }
    unproven_evaluation={
        **valid_evaluation,
        'calculation':{
            **valid_evaluation['calculation'],
            'settlement_profile':unproven_settlement,
        },
    }
    unproven=capture(
        tmp_path/'closing-unproven.sqlite3',unproven_evaluation,valid_quote
    )
    assert unproven['status']=='unavailable'
    assert unproven['reason_code']=='SETTLEMENT_PROFILE_CONTRADICTION'
    assert 'not proven' in unproven['reason']
    assert 'roi_pct' not in unproven

    unknown_quote=input_quote(
        total_cost='8',
        winning_payout='20',
        losing_return='1',
        observed_at=entered,
        settlement_profile={'profile_id':'test.synthetic.unknown','version':1},
    )
    unknown_evaluation=evaluate(
        unknown_quote,
        game,
        references(probability=.5,observed=entered),
        settings,
        [],
        entered,
        build_registry(()),
    )
    assert unknown_evaluation['calculation']['settlement_profile']['resolved'] is None
    assert unknown_evaluation['net'] is not None
    unknown=capture(
        tmp_path/'closing-unknown-profile.sqlite3',unknown_evaluation,unknown_quote
    )
    assert unknown['status']=='supported'
    assert unknown['roi_pct']==pytest.approx(31.25)
