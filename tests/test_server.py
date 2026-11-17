import json
import asyncio
import pytest
from fastapi.testclient import TestClient
from backend.main import app, SESSIONS
from backend.mcp_app import mcp, campus_venues, RESOURCE


def test_http_run_and_state_action():
    with TestClient(app) as client:
        health=client.get('/api/health').json()
        assert health['lessons'] == 23
        assert 'key' not in health
        result=client.post('/api/run',json={'lesson':'02.2','mode':'declarative'})
        assert result.status_code == 200
        rows=[json.loads(line[5:]) for line in result.text.splitlines() if line.startswith('data:')]
        payload=next(row['value'] for row in rows if row.get('name')=='campus.result')
        response=client.post('/api/action',json={'session':payload['session'],'action':'add_attendees'})
        assert response.json()['payload']['plan']['attendees']==90
        assert response.json()['events'][0]['type']=='STATE_DELTA'
        assert client.post('/api/action',json={'session':payload['session'],'action':'book_venue'}).status_code==422
        assert client.post('/api/run',json={'lesson':'99.9'}).status_code==404
        assert client.get('/.env').status_code==404
        assert client.get('/assets/../.env').status_code==404


def test_mcp_metadata_and_tool():
    tools=asyncio.run(mcp.list_tools())
    tool=next(t for t in tools if t.name=='campus_venues')
    assert tool.meta['ui']['resourceUri']==RESOURCE
    assert len(campus_venues(80)['venues'])==2
    assert campus_venues(80, 'mixed')['html'].startswith('<!doctype html>')
    with pytest.raises(ValueError):campus_venues(-1)
