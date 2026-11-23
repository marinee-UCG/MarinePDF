from backend.rag.prompt import NOT_FOUND_MESSAGE, build_prompt
from backend.rag.retriever import SearchHit


def test_prompt_contains_context_and_citation_labels():
    hits = [SearchHit("Clean seat and threads.", 101, "G09500", "Hydraulic Screw Tightenings", 0.2)]
    prompt = build_prompt("How to loosen?", hits)
    assert "Clean seat and threads." in prompt
    assert "G09500" in prompt and "101" in prompt
    assert "How to loosen?" in prompt


def test_prompt_instructs_grounding():
    prompt = build_prompt("q", [])
    assert NOT_FOUND_MESSAGE in prompt