from pydantic import BaseModel,Field,field_validator

class AskRequest(BaseModel):

    question:str=Field(min_length=3,max_length=1000)
    top_k:int=Field(default=5,ge=1,le=20)
    @field_validator("question",mode="before")
    @classmethod
    def strip_question(cls,value):
        if isinstance(value,str):
            return value.strip()
        return value

class SourceOut(BaseModel):
    section_code:str | None
    section_title:str | None
    page_number:int
    snippet:str

class AskResponse(BaseModel):
    answer:str
    sources:list[SourceOut]        