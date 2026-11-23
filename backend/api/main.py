from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.config import get_settings
from backend.ingestion.embedder import Embedder
from backend.api.routers import ask,health

@asynccontextmanager
async def lifespan(app:FastAPI):
    app.state.embedder=Embedder(get_settings().embedding_model)
    yield

app=FastAPI(title="MarinePDF",lifespan=lifespan)
app.include_router(health.router)
app.include_router(ask.router)