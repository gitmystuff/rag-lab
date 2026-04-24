from pydantic import BaseModel


class DocumentCreate(BaseModel):
    title: str
    source: str | None = None
