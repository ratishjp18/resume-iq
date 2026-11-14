# ResumeIQ architecture

```
React (Vite) ──Axios──▶ FastAPI routes (app/api)
                          ├─ Pydantic schemas (app/schemas)
                          ├─ document_parser   PDF (PyMuPDF) / DOCX (python-docx), in memory only
                          ├─ skill_extractor   catalog + aliases + negation (data/skills.json)
                          ├─ embedding         SentenceTransformer singleton, CPU, cached in backend/var/models
                          ├─ matcher           requirements, cosine similarity, status classification, metrics
                          ├─ recommender       rule-based templates (data/recommendations.json)
                          └─ SQLAlchemy models ──▶ SQLite (Alembic migrations)
```

## Matching algorithm (`services/matcher.py`)
1. **Requirements** = each non-negated catalog skill in the job description (`skill`) plus up to 12 requirement
   sentences containing no catalog skill (`statement`, detected by cue words such as "experience", "ability").
2. Resume and job text are split into sentence/bullet passages. Requirements (`"Experience with <skill>"` or the
   sentence) and passages are embedded with `all-MiniLM-L6-v2`; similarity is cosine (vectors are L2-normalised).
3. **Skill requirements**
   - explicit non-negated mention in the resume → `matched` (evidence = the mention passage with highest similarity,
     preferring passages that describe work over bare lists; `evidence_strength` = `demonstrated` | `listed`)
   - only a negated mention ("no experience with X") → `not_evidenced`
   - no mention, but a passage with a *different skill of the same category* has similarity ≥ 0.45, or any passage has
     similarity ≥ 0.50 → `uncertain` (never `matched`)
   - otherwise `not_evidenced`
4. **Statement requirements**: similarity ≥ 0.55 *and* at least one shared content word → `matched`; ≥ 0.55 without a
   shared word, or ≥ 0.40 → `uncertain`; else `not_evidenced`.

## Metrics
- **Requirement coverage** = matched / total identified × 100 (0 when nothing is identified; the UI shows a notice).
- **Semantic similarity** = mean over requirements of the best cosine similarity to any resume passage, clipped to
  [0, 1]. It is an index, not a probability or percentage.

## Thresholds
All thresholds are configurable (`RESUMEIQ_THRESHOLD_*`) and are **unvalidated defaults**: they were chosen by
inspection and must be tuned against labeled resume/job pairs before relying on them.

## Data model
`resumes`, `job_descriptions`, `analyses`, `skill_matches`, `recommendations` with FK `ON DELETE CASCADE`; SQLite
`PRAGMA foreign_keys=ON` on every connection; timestamps stored as UTC. Deleting a resume deletes its analyses; deleting
an analysis also removes the job description if no other analysis uses it.
`skill_matches` additionally stores `category`, `requirement_type`, `evidence_strength` and `note`.
