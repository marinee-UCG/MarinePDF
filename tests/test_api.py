import pytest
from fastapi.testclient import TestClient
from backend.api import deps
from backend.api.main import app
from backend.api.routers import ask
from backend.rag.llm import LLMError
from backend.rag.retriever import SearchHit
from backend.rag.service import Answer

class FakeSession():
    def execute(self,statement):
        return None

@pytest.fixture
def client():
    app.dependency_overrides[deps.get_db]=lambda:FakeSession()
    app.dependency_overrides[deps.get_embedder]=lambda:object()
    app.dependency_overrides[deps.get_llm_client]=lambda:object()

    yield TestClient(app)

    app.dependency_overrides.clear()

def test_health(client):
    response=client.get("/health")
    assert response.status_code == 200
    assert response.json()== {"status":"ok","db":"ok"}

def test_blank_question_rejected(client):
    response=client.post("/ask",json={"question":"  "})
    assert response.status_code == 422

def test_ask_returns_answer_and_sources(client,monkeypatch):
    hit=SearchHit("Clean seat and threads.",101,"G09500","Hydraulic Screw Tightenings",0.2)
    monkeypatch.setattr(ask,"answer_question",lambda *args,**kwargs:Answer("Do X.",[hit]))
    response=client.post("/ask",json={"question":"How to loosen?"})
    body=response.json()
    assert response.status_code == 200
    assert body["answer"] == "Do X."
    assert body["sources"][0]["page_number"] == 101
    assert body["sources"][0]["section_code"] == "G09500"

def test_llm_error_returns_503(client,monkeypatch):
    def boom(*args,**kwargs):
        raise LLMError("Groq down")
    monkeypatch.setattr(ask,"answer_question",boom)
    response=client.post("/ask",json={"question":"How to loosen?"})
    assert response.status_code == 503
    assert "LLM service unavailable" in response.json()["detail"] 
    
