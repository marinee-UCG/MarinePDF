import argparse

from backend.config import get_settings
from backend.db.database import SessionLocal
from backend.ingestion.embedder import Embedder
from backend.rag.llm import get_llm
from backend.rag.service import answer_question


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask a question about the engine manual")
    parser.add_argument("question")
    args = parser.parse_args()

    settings = get_settings()
    embedder = Embedder(settings.embedding_model)
    llm = get_llm(settings)

    with SessionLocal() as session:
        result = answer_question(args.question, session, embedder, llm)

    print("\n" + result.answer)
    if result.sources:
        print("\nRetrieved sources:")
        for hit in result.sources:
            print(f"  {hit.distance:.3f}  {hit.section_code}  p.{hit.page_number}  {hit.section_title}")


if __name__ == "__main__":
    main()
