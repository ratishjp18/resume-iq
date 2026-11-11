from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Status = Literal["matched", "not_evidenced", "uncertain"]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str
    version: str
    embedding_model: str
    model_loaded: bool


class ResumeOut(ORMModel):
    id: int
    original_filename: str
    file_type: str
    extracted_text: str
    char_count: int
    word_count: int
    created_at: datetime


class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    company_name: str | None = Field(default=None, max_length=200)
    description_text: str = Field(min_length=30, max_length=30_000)

    @field_validator("title", "description_text")
    @classmethod
    def _strip_required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("must not be blank")
        return v

    @field_validator("company_name")
    @classmethod
    def _strip_optional(cls, v: str | None) -> str | None:
        v = (v or "").strip()
        return v or None


class JobOut(ORMModel):
    id: int
    title: str
    company_name: str | None
    description_text: str
    created_at: datetime


class AnalysisCreate(BaseModel):
    resume_id: int = Field(gt=0)
    job_id: int = Field(gt=0)


class SkillMatchOut(ORMModel):
    skill_name: str
    status: Status
    category: str
    requirement_type: Literal["skill", "statement"]
    resume_evidence: str | None
    similarity_score: float | None
    evidence_strength: str | None = None
    note: str | None = None


class RecommendationOut(ORMModel):
    category: str
    message: str


class AnalysisOut(BaseModel):
    id: int
    resume_id: int
    job_id: int
    resume_filename: str
    job_title: str
    company_name: str | None
    coverage_score: float
    semantic_similarity: float
    requirements_total: int
    requirements_matched: int
    matched_skills: list[SkillMatchOut]
    not_evidenced_skills: list[SkillMatchOut]
    uncertain_skills: list[SkillMatchOut]
    recommendations: list[RecommendationOut]
    model_version: str
    created_at: datetime


class AnalysisSummary(BaseModel):
    id: int
    resume_id: int
    job_id: int
    resume_filename: str
    job_title: str
    company_name: str | None
    coverage_score: float
    semantic_similarity: float
    created_at: datetime


class AnalysisList(BaseModel):
    items: list[AnalysisSummary]
    total: int
