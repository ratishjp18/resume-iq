from datetime import datetime

from sqlalchemy import CheckConstraint, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, UTCDateTime, utcnow


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(10))
    extracted_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", passive_deletes=True
    )
    __table_args__ = (CheckConstraint("file_type IN ('pdf','docx')", name="ck_resume_file_type"),)


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description_text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    analyses: Mapped[list["Analysis"]] = relationship(
        back_populates="job", cascade="all, delete-orphan", passive_deletes=True
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_descriptions.id", ondelete="CASCADE"), index=True)
    coverage_score: Mapped[float] = mapped_column(Float)
    semantic_similarity: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)

    resume: Mapped[Resume] = relationship(back_populates="analyses")
    job: Mapped[JobDescription] = relationship(back_populates="analyses")
    skill_matches: Mapped[list["SkillMatch"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True, order_by="SkillMatch.id"
    )
    recommendations: Mapped[list["Recommendation"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", passive_deletes=True, order_by="Recommendation.id"
    )
    __table_args__ = (CheckConstraint("coverage_score >= 0 AND coverage_score <= 100", name="ck_coverage_range"),)


class SkillMatch(Base):
    __tablename__ = "skill_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    skill_name: Mapped[str] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(20))
    resume_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Additional explainability fields
    category: Mapped[str] = mapped_column(String(80), default="General")
    requirement_type: Mapped[str] = mapped_column(String(20), default="skill")
    evidence_strength: Mapped[str | None] = mapped_column(String(20), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis: Mapped[Analysis] = relationship(back_populates="skill_matches")
    __table_args__ = (
        CheckConstraint("status IN ('matched','not_evidenced','uncertain')", name="ck_match_status"),
        Index("ix_skill_matches_analysis_status", "analysis_id", "status"),
    )


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(40))
    message: Mapped[str] = mapped_column(Text)

    analysis: Mapped[Analysis] = relationship(back_populates="recommendations")
