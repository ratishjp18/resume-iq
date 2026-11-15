"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-11-15
"""
import sqlalchemy as sa
from alembic import op

from app.database import UTCDateTime

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("extracted_text", sa.Text, nullable=False),
        sa.Column("created_at", UTCDateTime, nullable=False),
        sa.CheckConstraint("file_type IN ('pdf','docx')", name="ck_resume_file_type"),
    )
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("company_name", sa.String(200)),
        sa.Column("description_text", sa.Text, nullable=False),
        sa.Column("created_at", UTCDateTime, nullable=False),
    )
    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resume_id", sa.Integer, sa.ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer, sa.ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("coverage_score", sa.Float, nullable=False),
        sa.Column("semantic_similarity", sa.Float, nullable=False),
        sa.Column("model_version", sa.String(200), nullable=False),
        sa.Column("created_at", UTCDateTime, nullable=False),
        sa.CheckConstraint("coverage_score >= 0 AND coverage_score <= 100", name="ck_coverage_range"),
    )
    op.create_index("ix_analyses_resume_id", "analyses", ["resume_id"])
    op.create_index("ix_analyses_job_id", "analyses", ["job_id"])
    op.create_index("ix_analyses_created_at", "analyses", ["created_at"])
    op.create_table(
        "skill_matches",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("analysis_id", sa.Integer, sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_name", sa.String(300), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("resume_evidence", sa.Text),
        sa.Column("similarity_score", sa.Float),
        sa.Column("category", sa.String(80), nullable=False, server_default="General"),
        sa.Column("requirement_type", sa.String(20), nullable=False, server_default="skill"),
        sa.Column("evidence_strength", sa.String(20)),
        sa.Column("note", sa.Text),
        sa.CheckConstraint("status IN ('matched','not_evidenced','uncertain')", name="ck_match_status"),
    )
    op.create_index("ix_skill_matches_analysis_id", "skill_matches", ["analysis_id"])
    op.create_index("ix_skill_matches_analysis_status", "skill_matches", ["analysis_id", "status"])
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("analysis_id", sa.Integer, sa.ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("message", sa.Text, nullable=False),
    )
    op.create_index("ix_recommendations_analysis_id", "recommendations", ["analysis_id"])


def downgrade() -> None:
    for table in ("recommendations", "skill_matches", "analyses", "job_descriptions", "resumes"):
        op.drop_table(table)
