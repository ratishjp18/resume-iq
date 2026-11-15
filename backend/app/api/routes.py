from typing import Literal

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app import __version__
from app.api.errors import NotFound
from app.config import Settings, get_settings
from app.database import get_db
from app.models import Analysis, JobDescription, Resume
from app.schemas import (
    AnalysisCreate, AnalysisList, AnalysisOut, ErrorResponse, HealthResponse, JobCreate, JobOut, ResumeOut,
)
from app.services import embedding
from app.services.analysis_service import list_analyses, load_analysis, run_analysis, to_out
from app.services.document_parser import DocumentError, parse_document

router = APIRouter(prefix="/api")
_ERR = {400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}, 413: {"model": ErrorResponse},
        415: {"model": ErrorResponse}, 422: {"model": ErrorResponse}}


def _resume_out(r: Resume) -> ResumeOut:
    return ResumeOut(
        id=r.id, original_filename=r.original_filename, file_type=r.file_type, extracted_text=r.extracted_text,
        char_count=len(r.extracted_text), word_count=len(r.extracted_text.split()), created_at=r.created_at,
    )


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health(settings: Settings = Depends(get_settings)):
    return HealthResponse(
        status="ok", version=__version__, embedding_model=settings.embedding_model,
        model_loaded=embedding._embedder is not None,
    )


@router.post("/resumes", response_model=ResumeOut, status_code=201, responses=_ERR, tags=["resumes"])
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    # Read at most limit+1 bytes so oversized uploads are rejected without loading them fully.
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise DocumentError("file_too_large", f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit.", 413)
    doc = parse_document(file.filename or "", data)
    resume = Resume(original_filename=doc.filename, file_type=doc.file_type, extracted_text=doc.text)
    db.add(resume)
    db.commit()
    return _resume_out(resume)


@router.get("/resumes/{resume_id}", response_model=ResumeOut, responses=_ERR, tags=["resumes"])
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.get(Resume, resume_id)
    if not resume:
        raise NotFound("Resume")
    return _resume_out(resume)


@router.delete("/resumes/{resume_id}", status_code=204, responses=_ERR, tags=["resumes"])
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    """Deletes the resume text and every analysis derived from it."""
    resume = db.get(Resume, resume_id)
    if not resume:
        raise NotFound("Resume")
    job_ids = set(db.scalars(select(Analysis.job_id).where(Analysis.resume_id == resume_id)))
    db.delete(resume)
    _delete_orphan_jobs(db, job_ids)
    db.commit()
    return Response(status_code=204)


@router.post("/jobs", response_model=JobOut, status_code=201, responses=_ERR, tags=["jobs"])
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    job = JobDescription(**payload.model_dump())
    db.add(job)
    db.commit()
    return job


@router.get("/jobs/{job_id}", response_model=JobOut, responses=_ERR, tags=["jobs"])
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.get(JobDescription, job_id)
    if not job:
        raise NotFound("Job description")
    return job


@router.post("/analyses", response_model=AnalysisOut, status_code=201, responses=_ERR, tags=["analyses"])
def create_analysis(
    payload: AnalysisCreate,
    db: Session = Depends(get_db),
    embedder=Depends(embedding.get_embedder),
    settings: Settings = Depends(get_settings),
):
    resume = db.get(Resume, payload.resume_id)
    if not resume:
        raise NotFound("Resume")
    job = db.get(JobDescription, payload.job_id)
    if not job:
        raise NotFound("Job description")
    analysis = run_analysis(db, resume, job, embedder, settings)
    return to_out(load_analysis(db, analysis.id))


@router.get("/analyses", response_model=AnalysisList, tags=["analyses"])
def get_analyses(
    q: str | None = Query(None, max_length=100, description="Search job title / company"),
    sort_by: Literal["date", "coverage", "similarity", "job_title"] = "date",
    order: Literal["asc", "desc"] = "desc",
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    items, total = list_analyses(db, q, sort_by, order, limit, offset)
    return AnalysisList(items=items, total=total)


@router.get("/analyses/{analysis_id}", response_model=AnalysisOut, responses=_ERR, tags=["analyses"])
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = load_analysis(db, analysis_id)
    if not analysis:
        raise NotFound("Analysis")
    return to_out(analysis)


@router.delete("/analyses/{analysis_id}", status_code=204, responses=_ERR, tags=["analyses"])
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = db.get(Analysis, analysis_id)
    if not analysis:
        raise NotFound("Analysis")
    job_id = analysis.job_id
    db.delete(analysis)
    _delete_orphan_jobs(db, {job_id})
    db.commit()
    return Response(status_code=204)


def _delete_orphan_jobs(db: Session, job_ids: set[int]) -> None:
    """Remove job descriptions that no longer have any analysis (they only exist to support one)."""
    db.flush()
    for job_id in job_ids:
        if not db.scalar(select(func.count()).select_from(Analysis).where(Analysis.job_id == job_id)):
            job = db.get(JobDescription, job_id)
            if job:
                db.delete(job)
