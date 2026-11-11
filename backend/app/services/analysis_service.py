"""Orchestrates matching, recommendation and persistence for an analysis."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import Settings
from app.models import Analysis, JobDescription, Recommendation, Resume, SkillMatch
from app.schemas import AnalysisOut, AnalysisSummary, RecommendationOut, SkillMatchOut
from app.services.embedding import Embedder
from app.services.matcher import MATCHER_VERSION, match_resume
from app.services.recommender import recommend


def run_analysis(db: Session, resume: Resume, job: JobDescription, embedder: Embedder, settings: Settings) -> Analysis:
    outcome = match_resume(resume.extracted_text, job.description_text, embedder, settings)
    analysis = Analysis(
        resume_id=resume.id,
        job_id=job.id,
        coverage_score=outcome.coverage,
        semantic_similarity=outcome.semantic_similarity,
        model_version=f"{embedder.model_name} | {MATCHER_VERSION}",
    )
    analysis.skill_matches = [
        SkillMatch(
            skill_name=m.name, status=m.status, resume_evidence=m.evidence, similarity_score=m.similarity,
            category=m.category, requirement_type=m.requirement_type, evidence_strength=m.evidence_strength, note=m.note,
        )
        for m in outcome.matches
    ]
    analysis.recommendations = [
        Recommendation(category=c, message=msg) for c, msg in recommend(outcome.matches, resume.extracted_text)
    ]
    db.add(analysis)
    db.commit()
    return analysis


def load_analysis(db: Session, analysis_id: int) -> Analysis | None:
    stmt = (
        select(Analysis)
        .where(Analysis.id == analysis_id)
        .options(selectinload(Analysis.skill_matches), selectinload(Analysis.recommendations))
    )
    return db.execute(stmt).scalar_one_or_none()


def to_out(a: Analysis) -> AnalysisOut:
    matches = [SkillMatchOut.model_validate(m) for m in a.skill_matches]
    by = lambda s: [m for m in matches if m.status == s]  # noqa: E731
    return AnalysisOut(
        id=a.id, resume_id=a.resume_id, job_id=a.job_id, resume_filename=a.resume.original_filename,
        job_title=a.job.title, company_name=a.job.company_name, coverage_score=a.coverage_score,
        semantic_similarity=a.semantic_similarity, requirements_total=len(matches),
        requirements_matched=len(by("matched")), matched_skills=by("matched"),
        not_evidenced_skills=by("not_evidenced"), uncertain_skills=by("uncertain"),
        recommendations=[RecommendationOut.model_validate(r) for r in a.recommendations],
        model_version=a.model_version, created_at=a.created_at,
    )


_SORTS = {
    "date": Analysis.created_at,
    "coverage": Analysis.coverage_score,
    "similarity": Analysis.semantic_similarity,
    "job_title": JobDescription.title,
}


def list_analyses(db: Session, q: str | None, sort_by: str, order: str, limit: int, offset: int):
    stmt = select(Analysis).join(Analysis.job).join(Analysis.resume).options(selectinload(Analysis.job), selectinload(Analysis.resume))
    if q:
        like = f"%{q.strip().lower()}%"
        stmt = stmt.where(
            func.lower(JobDescription.title).like(like) | func.lower(func.coalesce(JobDescription.company_name, "")).like(like)
        )
    total = db.execute(select(func.count()).select_from(stmt.order_by(None).subquery())).scalar_one()
    col = _SORTS.get(sort_by, Analysis.created_at)
    stmt = stmt.order_by(col.asc() if order == "asc" else col.desc(), Analysis.id.desc()).limit(limit).offset(offset)
    rows = db.execute(stmt).scalars().all()
    items = [
        AnalysisSummary(
            id=a.id, resume_id=a.resume_id, job_id=a.job_id, resume_filename=a.resume.original_filename,
            job_title=a.job.title, company_name=a.job.company_name, coverage_score=a.coverage_score,
            semantic_similarity=a.semantic_similarity, created_at=a.created_at,
        )
        for a in rows
    ]
    return items, total
