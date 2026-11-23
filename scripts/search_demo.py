from backend.config import get_settings
from backend.rag.retriever import search
from backend.ingestion.embedder import Embedder
from backend.db.database import SessionLocal

QUESTIONS=["How do i loosen a hydraulic screw ?","Engine stopping procedure","Turbocharger maintenance","Fuel injection valve tightening torque"]

embedder=Embedder(get_settings().embedding_model)
with SessionLocal() as session:
    for question in QUESTIONS:
        query_vector=embedder.embed_query(question)
        hits=search(session,query_vector)
        print(f"\n=== {question}")
        for hit in hits:
            print(f"{hit.distance:.3f} p.{hit.page_number} {hit.section_code} {hit.section_title}")