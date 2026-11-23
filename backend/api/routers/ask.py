from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session

from backend.api.schemas import AskRequest,AskResponse,SourceOut
from backend.api.deps import get_db,get_embedder,get_llm_client
from backend.ingestion.embedder import Embedder
from backend.rag.llm import LLMClient,LLMError
from backend.rag.service import answer_question

SNIPPET_LENGTH = 300

router=APIRouter(tags=["ask"])

@router.post("/ask",response_model=AskResponse)
def ask(
    request:AskRequest,
    db:Session=Depends(get_db),
    embedder:Embedder=Depends(get_embedder),
    llm:LLMClient=Depends(get_llm_client),
) -> AskResponse:
    try:
        result=answer_question(request.question,db,embedder,llm,top_k=request.top_k)
    except LLMError as exc:
        raise HTTPException(status_code=503,detail=f"LLM service unavailable: {exc}") from exc
    sources=[]
    for hit in result.sources:
        sources.append(SourceOut(section_code=hit.section_code,section_title=hit.section_title,page_number=hit.page_number,snippet=hit.content[:SNIPPET_LENGTH]))
    return AskResponse(answer=result.answer,sources=sources)
    