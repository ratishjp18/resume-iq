# REST API

Base URL `http://localhost:8000`. Interactive docs: `/docs` (Swagger) and `/redoc`.

Errors always look like `{"error": {"code": "...", "message": "...", "details": [{"field","message"}]?}}`.

| Method | Path | Description | Success |
|---|---|---|---|
| GET | `/api/health` | Status, version, model name, whether the model is loaded | 200 |
| POST | `/api/resumes` | Multipart `file` (PDF/DOCX, ≤ 5 MB). Returns id, extracted text, word count | 201 |
| GET | `/api/resumes/{id}` | Fetch stored resume text/metadata | 200 |
| DELETE | `/api/resumes/{id}` | Delete resume and all its analyses | 204 |
| POST | `/api/jobs` | `{title, company_name?, description_text}` (description 30–30,000 chars) | 201 |
| GET | `/api/jobs/{id}` | Fetch a job description | 200 |
| POST | `/api/analyses` | `{resume_id, job_id}` runs the analysis | 201 |
| GET | `/api/analyses` | Query: `q`, `sort_by` (date/coverage/similarity/job_title), `order`, `limit`, `offset` | 200 |
| GET | `/api/analyses/{id}` | Full analysis | 200 |
| DELETE | `/api/analyses/{id}` | Delete one analysis | 204 |

Error codes: `unsupported_file_type` (415), `content_mismatch` (415), `file_too_large` (413), `empty_file`,
`corrupted_file`, `encrypted_file`, `no_extractable_text` (422, scanned PDFs need OCR), `validation_error` (422),
`not_found` (404).

## Analysis response
`id, resume_id, job_id, resume_filename, job_title, company_name, coverage_score (0-100), semantic_similarity (0-1),
requirements_total, requirements_matched, matched_skills[], not_evidenced_skills[], uncertain_skills[],
recommendations[{category,message}], model_version, created_at (UTC)`.
Each skill item: `skill_name, status, category, requirement_type, resume_evidence, similarity_score, evidence_strength, note`.
