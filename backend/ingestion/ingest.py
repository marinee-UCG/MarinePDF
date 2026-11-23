import argparse
from pathlib import Path
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db.models import Chunk,Document
from backend.config import get_settings
from backend.db.database import init_db,SessionLocal
from backend.ingestion.pdf_reader import read_pages
from backend.ingestion.embedder import Embedder
from backend.ingestion.chunker import chunk_pages

def ingest_pdf(pdf_path:Path,session:Session,embedder:Embedder) -> int:
    pages=read_pages(pdf_path)
    text_chunks=chunk_pages(pages)
    existing=session.scalar(select(Document).where(Document.filename == pdf_path.name))
    if existing:
        session.delete(existing)
        session.flush()
    texts=[]
    for text_chunk in text_chunks:
        texts.append(text_chunk.content)
    vectors=embedder.embed_documents(texts)
    document=Document(filename=pdf_path.name,page_count=len(pages))
    for text_chunk,vector in zip(text_chunks,vectors):
        db_chunk=Chunk(page_number=text_chunk.page_number,section_code=text_chunk.section_code,section_title=text_chunk.section_title,content=text_chunk.content,embedding=vector)
        document.chunks.append(db_chunk)
    session.add(document)
    session.commit()
    return len(text_chunks)

def main() -> None:
    parser=argparse.ArgumentParser(description="Ingest a PDF manual into the vector database")
    parser.add_argument("pdf_path",type=Path)
    args=parser.parse_args()
    init_db()
    embedder=Embedder(get_settings().embedding_model)
    with SessionLocal() as session:
        count=ingest_pdf(args.pdf_path,session,embedder)
        print(f"Ingested {count} chunks from {args.pdf_path.name}")

if __name__=="__main__":
    main()

