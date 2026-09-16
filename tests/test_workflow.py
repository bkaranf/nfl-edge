import asyncio
from datetime import timedelta
import json

import httpx
from fastapi.testclient import TestClient
import pytest

from backend.app import create_app
from backend.domain import iso, utcnow
from backend.providers import fetch_kalshi, parse_bovada, parse_espn, parse_kalshi
from backend.service import Service
from backend.storage import Store
from tests.test_engine import GAME, NOW, SETTINGS, input_quote, pair, references


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
        assert result['qualified']
        assert client.post('/api/bets',json={**raw,'mode':'actual'}).status_code==422
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
    from backend.engine import evaluate
    entered=start-timedelta(hours=1)
    q=input_quote(observed_at=entered)
    evaluation=evaluate(q,g,references(observed=entered),SETTINGS,[],entered)
    store.add_bet({'quote':q.model_dump(mode='json'),'game':g,'evaluation':evaluation,'notes':'','audit':[]})
    after=start+timedelta(seconds=1)
    store.put_source('fixture',{'status':'ok'},{'observed_at':iso(after),'quotes':references(observed=after)})
    Service(store).capture_closing()
    assert store.bets()[0]['closing']['status']=='unavailable'
