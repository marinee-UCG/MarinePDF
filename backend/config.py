from functools import lru_cache
from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config=SettingsConfigDict(env_file=".env")
    database_url:str
    groq_api_key:str = ""
    llm_provider:str ="groq"
    llm_model:str = "qwen/qwen3.8-27b"
    embedding_model:str="BAAI/bge-small-en-v1.5"
    api_url:str="http://localhost:8000"

@lru_cache
def get_settings() ->Settings:
    return Settings()