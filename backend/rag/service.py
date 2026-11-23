from dataclasses import dataclass
from sqlalchemy.orm import Session

from backend.ingestion.embedder import Embedder
from backend.rag.llm import LLMClient
from backend.rag.prompt import NOT_FOUND_MESSAGE, build_prompt
from backend.rag.retriever import SearchHit, search


@dataclass
class Answer:
    answer: str
    sources: list[SearchHit]


def answer_question(
    question: str,
    session: Session,
    embedder: Embedder,
    llm: LLMClient,
    top_k: int = 5,
    max_distance: float = 0.4,
) -> Answer:
    query_vector = embedder.embed_query(question)
    hits = search(session, query_vector, top_k)

    relevant = []
    for hit in hits:
        if hit.distance <= max_distance:
            relevant.append(hit)

    if not relevant:
        return Answer(answer=NOT_FOUND_MESSAGE, sources=[])

    prompt = build_prompt(question, relevant)
    text = llm.generate(prompt)
    return Answer(answer=text, sources=relevant)
