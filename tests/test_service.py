import pytest

from backend.rag import service
from backend.rag.llm import LLMError
from backend.rag.prompt import NOT_FOUND_MESSAGE
from backend.rag.retriever import SearchHit


class FakeEmbedder:
    def embed_query(self, text):
        return [0.0] * 384


class FakeLLM:
    def __init__(self, reply="ANSWER", error=None):
        self.reply = reply
        self.error = error
        self.calls = 0

    def generate(self, prompt):
        self.calls += 1
        if self.error:
            raise self.error
        return self.reply


def hit(distance):
    return SearchHit("Clean seat and threads.", 101, "G09500", "Hydraulic Screw Tightenings", distance)


def test_no_relevant_hits_returns_not_found_without_calling_llm(monkeypatch):
    monkeypatch.setattr(service, "search", lambda session, vector, top_k: [hit(0.6), hit(0.7)])
    llm = FakeLLM()
    result = service.answer_question("capital of France?", None, FakeEmbedder(), llm)
    assert result.answer == NOT_FOUND_MESSAGE
    assert result.sources == []
    assert llm.calls == 0


def test_relevant_hits_passed_to_llm_and_returned_as_sources(monkeypatch):
    monkeypatch.setattr(service, "search", lambda session, vector, top_k: [hit(0.2), hit(0.3), hit(0.6)])
    result = service.answer_question("how to loosen?", None, FakeEmbedder(), FakeLLM("ANSWER"))
    assert result.answer == "ANSWER"
    assert len(result.sources) == 2


def test_llm_error_propagates(monkeypatch):
    monkeypatch.setattr(service, "search", lambda session, vector, top_k: [hit(0.2)])
    with pytest.raises(LLMError):
        service.answer_question("q", None, FakeEmbedder(), FakeLLM(error=LLMError("down")))
