from sqlalchemy import select
from dataclasses import dataclass
from sqlalchemy.orm import Session
from backend.db.models import Chunk


@dataclass
class SearchHit:
    content:str
    page_number:int
    section_code:str | None
    section_title:str | None
    distance:float

def search(session:Session,query_embedding:list[float],top_k:int = 5) ->list[SearchHit]:
    distance=Chunk.embedding.cosine_distance(query_embedding).label("distance")
    query=select(Chunk,distance).order_by(distance).limit(top_k)
    rows=session.execute(query).all()
    hits=[]
    for chunk,dist in rows:
        searchit=SearchHit(content=chunk.content,page_number=chunk.page_number,section_code=chunk.section_code,section_title=chunk.section_title,distance=dist)
        hits.append(searchit)
    return hits