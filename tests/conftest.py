import sys
import asyncio
from pathlib import Path
from collections import defaultdict
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import server
from storage import Store
from workspaces import Workspaces
from fastapi.testclient import TestClient

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'DATA',tmp_path)
    monkeypatch.setattr(server,'store',Store(tmp_path/'projectpilot.sqlite3'))
    monkeypatch.setattr(server,'ws',Workspaces(tmp_path/'projects'))
    monkeypatch.setattr(server,'jobs',{})
    monkeypatch.setattr(server,'locks',defaultdict(asyncio.Lock))
    monkeypatch.setattr(server,'dispatch_lock',asyncio.Lock())
    monkeypatch.setattr(server,'TOKEN','')
    monkeypatch.delenv('PP_SANDBOX_IMAGE',raising=False)
    monkeypatch.delenv('OPENROUTER_API_KEY',raising=False)
    with TestClient(server.app,headers={'X-ProjectPilot-Client':'workspace'}) as c: yield c
    server.store.close()
