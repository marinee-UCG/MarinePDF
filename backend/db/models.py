from datetime import datetime
from sqlalchemy import ForeignKey,String,Text,func
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column,relationship
from pgvector.sqlalchemy import Vector


EMBEDDING_DIM=384

class Base(DeclarativeBase):
    pass

class Document(Base):
    __tablename__="documents"

    id:Mapped[int]=mapped_column(primary_key=True)
    filename:Mapped[str]=mapped_column(String(255),unique=True)
    page_count:Mapped[int]
    created_at:Mapped[datetime]=mapped_column(server_default=func.now())
    chunks:Mapped[list["Chunk"]]=relationship(back_populates="document",cascade="all,delete-orphan")

class Chunk(Base):
    __tablename__="chunks"

    id:Mapped[int]=mapped_column(primary_key=True)
    document_id:Mapped[int]=mapped_column(ForeignKey("documents.id",ondelete="CASCADE"))
    page_number:Mapped[int]
    section_code:Mapped[str| None]=mapped_column(String(10))
    section_title:Mapped[str | None]=mapped_column(String(255))
    content:Mapped[str]=mapped_column(Text)
    embedding:Mapped[list[float]]=mapped_column(Vector(EMBEDDING_DIM))
    document:Mapped["Document"]=relationship(back_populates="chunks")