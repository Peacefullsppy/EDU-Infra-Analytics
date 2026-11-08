"""Testes isolados do agente, sem conexão de rede nem leitura física real."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import httpx
import pytest

FILE=Path(__file__).resolve().parents[3]/'agent'/'agent.py'
spec=importlib.util.spec_from_file_location('edu_infra_agent', FILE)
agent=importlib.util.module_from_spec(spec)
spec.loader.exec_module(agent)


def env(monkeypatch, **overrides):
    values={"EDU_API_URL":"https://host.example.ts.net", "EDU_COMPUTER_ID":"7", "EDU_AGENT_TOKEN":"eia_safe_test_token", "EDU_INTERVAL_SECONDS":"60", "EDU_DISK_PATH":"/"}
    values.update(overrides)
    for key,val in values.items():
        monkeypatch.setenv(key,val)


@pytest.mark.unit
@pytest.mark.parametrize('url,valid', [
    ('https://host.example.ts.net',True),('https://host.example.ts.net/',True),
    ('http://127.0.0.1:8000',True),('http://localhost:8000',True),
    ('http://[::1]:8000',True),('http://192.168.1.20:8000',False),
    ('http://example.com:8000',False),('ftp://server.com',False),
    ('',False),('not-a-url',False),
])
def test_agent_requires_tls_for_remote_connections(monkeypatch,url,valid):
    env(monkeypatch,EDU_API_URL=url)
    if valid:
        assert agent.configuration()[0]==url.rstrip('/')
    else:
        with pytest.raises(ValueError): agent.configuration()


@pytest.mark.unit
@pytest.mark.parametrize('key,value', [
    ('EDU_COMPUTER_ID','0'),('EDU_COMPUTER_ID','-1'),
    ('EDU_AGENT_TOKEN',''),('EDU_AGENT_TOKEN','plain')
])
def test_agent_requires_valid_identity(monkeypatch,key,value):
    env(monkeypatch,**{key:value})
    with pytest.raises(ValueError): agent.configuration()


@pytest.mark.unit
@pytest.mark.parametrize('seconds,expected', [('1',10),('9',10),('10',10),('60',60),('120',120)])
def test_agent_interval_minimum(monkeypatch,seconds,expected):
    env(monkeypatch,EDU_INTERVAL_SECONDS=seconds)
    assert agent.configuration()[3]==expected


@pytest.mark.unit
def test_agent_collects_machine_utilization(monkeypatch):
    monkeypatch.setattr(agent.psutil,'cpu_percent',lambda interval: 33.5)
    monkeypatch.setattr(agent.psutil,'virtual_memory',lambda:SimpleNamespace(percent=42.1))
    monkeypatch.setattr(agent.psutil,'disk_usage',lambda path:SimpleNamespace(percent=51.9))
    monkeypatch.setattr(agent.psutil,'boot_time',lambda:100.0)
    monkeypatch.setattr(agent.time,'time',lambda:300.0)
    monkeypatch.setattr(agent.platform,'system',lambda:'Windows')
    monkeypatch.setattr(agent.platform,'release',lambda:'11')
    measured=agent.collect('C:\\')
    assert measured['cpu_percent']==33.5 and measured['memory_percent']==42.1
    assert measured['disk_percent']==51.9 and measured['uptime_seconds']==200
    assert measured['os_name']=='Windows 11'
    assert measured['collected_at'].endswith('+00:00')


@pytest.mark.unit
def test_agent_sends_expected_header_and_payload():
    observed=[]
    def handler(req):
        observed.append(req)
        return httpx.Response(201,json={'id':123,'received':True})
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        response=agent.send(client,'https://host.example.ts.net',5,'eia_token',{'cpu_percent':42})
    assert response=={'id':123,'received':True}
    assert observed[0].url.path=='/api/agent/metrics'
    assert observed[0].headers['X-Agent-Token']=='eia_token'
    assert observed[0].headers['X-Computer-ID']=='5'
    assert '"cpu_percent":42' in observed[0].content.decode()


@pytest.mark.unit
@pytest.mark.parametrize('code', [400,401,403,404,409,500,503])
def test_agent_surfaces_api_error_codes(code):
    with httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(code,json={'detail':'failed'}))) as client:
        with pytest.raises(httpx.HTTPStatusError):
            agent.send(client,'https://host.example.ts.net',5,'eia_token',{'cpu_percent':42})


@pytest.mark.unit
def test_agent_once_stops_after_single_send(monkeypatch):
    env(monkeypatch)
    sent=[]
    class Client:
        def __init__(self,*a,**kw): pass
        def __enter__(self): return self
        def __exit__(self,*a): return False
    monkeypatch.setattr(agent.httpx,'Client',Client)
    monkeypatch.setattr(agent,'collect',lambda disk: {'cpu_percent':10.0,'memory_percent':20.0,'disk_percent':30.0})
    monkeypatch.setattr(agent,'send',lambda client,url,computer_id,token,metric:sent.append(computer_id) or {'id':1})
    agent.run(once=True)
    assert sent==[7]


@pytest.mark.unit
def test_agent_once_exits_nonzero_on_network_error(monkeypatch):
    env(monkeypatch)
    class Client:
        def __init__(self,*a,**kw): pass
        def __enter__(self): return self
        def __exit__(self,*a): return False
    monkeypatch.setattr(agent.httpx,'Client',Client)
    monkeypatch.setattr(agent,'collect',lambda disk: {'cpu_percent':10.0,'memory_percent':20.0,'disk_percent':30.0})
    def broken(*a,**kw): raise httpx.ConnectError('network failure')
    monkeypatch.setattr(agent,'send',broken)
    with pytest.raises(SystemExit) as err: agent.run(once=True)
    assert err.value.code==1
