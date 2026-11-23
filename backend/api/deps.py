from collections.abc import Iterator
from fastapi import HTTPException,Request
from sqlalchemy.orm import Session

from backend.rag.llm import LLMError,LLMClient,get_llm
from backend.config import get_settings
from backend.ingestion.embedder import Embedder
from backend.db.database import SessionLocal


def get_db() -> Iterator[Session]:
    with SessionLocal() as session:
        yield session

def get_embedder(request:Request) -> Embedder:
    return request.app.state.embedder

def get_llm_client() -> LLMClient:
    try:
        return get_llm(get_settings())
    except LLMError as exc:
        raise HTTPException(status_code=503,detail=f"LLM service unavailable {exc}") from exc
    
