from typing import Literal, Optional

from pydantic import BaseModel, Field


class ResumeParseData(BaseModel):
    filename: str
    format: Literal["pdf", "docx"]
    size_bytes: int = Field(..., ge=0)
    page_count: Optional[int] = Field(default=None, ge=0)
    character_count: int = Field(..., ge=0)
    word_count: int = Field(..., ge=0)
    text: str


class ResumeParseMeta(BaseModel):
    job_title: str
    company_name: Optional[str] = None
    job_description_length: int = Field(..., ge=0)
