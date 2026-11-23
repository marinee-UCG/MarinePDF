from sqlalchemy import create_engine,text
from sqlalchemy.orm import sessionmaker
from backend.config import get_settings
from backend.db.models import Base

engine=create_engine(get_settings().database_url)
SessionLocal=sessionmaker(bind=engine)

def init_db():
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(engine)
    