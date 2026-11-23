from typing import Protocol
from groq import Groq
from backend.config import Settings

class LLMError(Exception):
    pass

class LLMClient(Protocol):
    def generate(self,prompt:str) -> str: ...

class GroqClient:

    def __init__(self,api_key:str,model:str):
        if not api_key:
            raise LLMError("GROQ_API_KEY is not set")
        self.client=Groq(api_key=api_key)
        self.model=model

    def generate(self,prompt:str) -> str:
        try:
            response=self.client.chat.completions.create(
                model=self.model,
                messages=[{"role":"user","content":prompt}],
                temperature=0.1,
            )
        except Exception as exc:
            raise LLMError(f"Groq request failed: {exc}") from exc
        return response.choices[0].message.content

def get_llm(settings:Settings) -> LLMClient:
    if settings.llm_provider == "groq":
        return GroqClient(settings.groq_api_key,settings.llm_model)
    raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
