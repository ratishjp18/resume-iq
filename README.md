# ResumeIQ

**Understand Your Resume. Discover Your Skill Gaps. Prepare for Your Next Opportunity.**

ResumeIQ is a local, privacy-first resume analysis and job-description matching app. It extracts skills, finds the resume
evidence behind each job requirement using real sentence embeddings, reports skill gaps, and suggests next steps. No paid
APIs, no GPU, no cloud: everything runs on your CPU.

## Features
- PDF/DOCX upload with content validation, 5 MB limit, text preview; scanned PDFs rejected with an OCR explanation
- Catalog-based skill extraction with aliases, word-boundary matching (no "Java" in "JavaScript") and negation detection
- Semantic matching with `sentence-transformers/all-MiniLM-L6-v2` (loaded once, cached locally)
- Matched / Uncertain / Not-evidenced requirements, each with supporting resume passages
- Two separate metrics: requirement coverage and semantic similarity, with documented limitations
- Deterministic, rule-based recommendations (nothing fabricated)
- History with search, sort, reopen, delete analysis, delete saved resume data

## Stack
React + Vite, Tailwind, React Router, Axios, Recharts, Framer Motion, Lucide · FastAPI, Pydantic, SQLAlchemy, Alembic,
SQLite · Sentence Transformers, scikit-learn/NumPy · PyMuPDF, python-docx · Pytest, Vitest + Testing Library.

## Architecture
See [docs/architecture.md](docs/architecture.md) and [docs/api.md](docs/api.md).

## Screenshots
_Not included yet. Run the app and add screenshots to `docs/screenshots/`._

## Structure
```
backend/  app/{api,models,schemas,services,data}, migrations/, tests/, requirements.txt, alembic.ini
frontend/ src/{components,pages,hooks,services,utils,__tests__}
docs/     architecture.md, api.md
```

## Setup
Requirements: Python 3.11 (3.12 should work), Node 18+. Roughly 2 GB free disk (PyTorch CPU) and 4 GB RAM.
**First run downloads the ~90 MB embedding model once** (cached in `backend/var/models`); afterwards it works offline.

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
cp .env.example .env              # optional
alembic upgrade head              # creates backend/var/resumeiq.db (also run automatically on startup)
uvicorn app.main:app --port 8000  # http://localhost:8000/docs

# Frontend (second terminal)
cd frontend
cp .env.example .env              # VITE_API_URL=http://localhost:8000
npm install
npm run dev                       # http://localhost:5173
```
If port 8000 is busy, start the backend on another port and set `VITE_API_URL` accordingly.

## Tests
```bash
cd backend && pytest                  # fast unit/API tests (mocked embedder)
cd backend && pytest -m integration   # runs the real MiniLM model (downloads it on first use)
cd frontend && npm test
```

## Machine-learning methodology and scoring
- **Requirement coverage** = supported requirements / identified requirements × 100. A skill is supported only by an
  explicit, non-negated mention; embeddings choose the best evidence passage but cannot, alone, mark a skill as present.
- **Semantic similarity** = mean of each requirement's best cosine similarity with any resume passage (0–1). It is not a
  calibrated probability and not a percentage.
- Requirement sentences without a catalog skill need similarity ≥ 0.55 plus a shared key term to count as matched.
- Thresholds are **unvalidated defaults** and require evaluation on labeled examples. Neither metric is an ATS score or a
  hiring probability. "Not evidenced" means the resume text does not show it, not that the candidate lacks the skill.

## Privacy
Single-user local app. Uploaded files are parsed in memory and never stored; only extracted text and analysis results go to
local SQLite. Resume text is not logged. CORS is limited to the local dev origin. Delete endpoints/UI remove data. The repo
`.gitignore` excludes databases, model caches, `.env` and resume files. **Do not expose the backend publicly without adding
authentication, authorization and data protection.**

## Known limitations / future work
OCR for scanned PDFs · labeled evaluation set and threshold calibration · larger/extensible skill catalog (e.g. ESCO) ·
non-skill requirements (degrees, years of experience) · authentication for multi-user use · Docker packaging · screenshots.

## License
MIT, see [LICENSE](LICENSE).
