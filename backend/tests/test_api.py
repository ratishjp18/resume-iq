import io
import zipfile

from sqlalchemy import func, select, text

from app.models import Analysis, JobDescription, Recommendation, Resume, SkillMatch
from tests.conftest import make_blank_pdf, make_docx, make_pdf
from tests.sample_data import JOB_TEXT, RESUME_TEXT


def upload(client, name, data, ctype="application/octet-stream"):
    return client.post("/api/resumes", files={"file": (name, data, ctype)})


def make_analysis(client):
    r = upload(client, "resume.pdf", make_pdf(RESUME_TEXT)).json()
    j = client.post("/api/jobs", json={"title": "Backend Engineer", "company_name": "Acme", "description_text": JOB_TEXT}).json()
    resp = client.post("/api/analyses", json={"resume_id": r["id"], "job_id": j["id"]})
    return r, j, resp


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok" and "MiniLM" in body["embedding_model"]


def test_cors_allows_only_dev_origin(client):
    ok = client.options("/api/health", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    bad = client.options("/api/health", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-origin" not in bad.headers


def test_upload_valid_pdf(client):
    resp = upload(client, "resume.pdf", make_pdf(RESUME_TEXT))
    assert resp.status_code == 201
    body = resp.json()
    assert body["file_type"] == "pdf" and "FastAPI" in body["extracted_text"] and body["word_count"] > 20
    assert client.get(f"/api/resumes/{body['id']}").json()["id"] == body["id"]


def test_upload_valid_docx(client):
    resp = upload(client, "cv.docx", make_docx(RESUME_TEXT))
    assert resp.status_code == 201 and resp.json()["file_type"] == "docx"
    assert "PostgreSQL" in resp.json()["extracted_text"]


def test_rejects_unsupported_extension(client):
    resp = upload(client, "resume.txt", b"hello world")
    assert resp.status_code == 415 and resp.json()["error"]["code"] == "unsupported_file_type"


def test_rejects_extension_content_mismatch(client):
    assert upload(client, "fake.pdf", make_docx(RESUME_TEXT)).status_code == 415
    assert upload(client, "fake.docx", make_pdf(RESUME_TEXT)).status_code == 415


def test_rejects_oversized(client):
    resp = upload(client, "big.pdf", b"%PDF-" + b"0" * (5 * 1024 * 1024 + 10))
    assert resp.status_code == 413 and resp.json()["error"]["code"] == "file_too_large"


def test_rejects_empty_file(client):
    assert upload(client, "empty.pdf", b"").status_code == 422


def test_rejects_corrupted_documents(client):
    assert upload(client, "bad.pdf", b"%PDF-1.4 this is not really a pdf").json()["error"]["code"] == "corrupted_file"
    assert upload(client, "bad.docx", b"PK\x03\x04garbage").json()["error"]["code"] == "corrupted_file"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("hello.txt", "x")
    assert upload(client, "zip.docx", buf.getvalue()).status_code == 415


def test_rejects_scanned_pdf_without_text(client):
    resp = upload(client, "scan.pdf", make_blank_pdf())
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "no_extractable_text" and "OCR" in resp.json()["error"]["message"]


def test_filename_path_is_stripped(client):
    resp = upload(client, "../../etc/resume.pdf", make_pdf(RESUME_TEXT))
    assert resp.json()["original_filename"] == "resume.pdf"


def test_job_validation_and_roundtrip(client):
    assert client.post("/api/jobs", json={"title": "", "description_text": "short"}).status_code == 422
    err = client.post("/api/jobs", json={"title": "Dev", "description_text": "x" * 20}).json()["error"]
    assert err["code"] == "validation_error" and err["details"]
    ok = client.post("/api/jobs", json={"title": " Dev ", "company_name": "  ", "description_text": JOB_TEXT})
    assert ok.status_code == 201 and ok.json()["title"] == "Dev" and ok.json()["company_name"] is None
    assert client.get(f"/api/jobs/{ok.json()['id']}").status_code == 200


def test_not_found_errors(client):
    for path in ["/api/resumes/99", "/api/jobs/99", "/api/analyses/99"]:
        r = client.get(path)
        assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
    assert client.post("/api/analyses", json={"resume_id": 1, "job_id": 1}).status_code == 404
    assert client.delete("/api/analyses/99").status_code == 404


def test_analysis_response_shape_and_persistence(client, session_factory):
    r, j, resp = make_analysis(client)
    assert resp.status_code == 201
    a = resp.json()
    for key in ["id", "resume_id", "job_id", "coverage_score", "semantic_similarity", "matched_skills",
                "not_evidenced_skills", "uncertain_skills", "recommendations", "model_version", "created_at"]:
        assert key in a
    assert a["resume_id"] == r["id"] and a["job_id"] == j["id"]
    assert a["requirements_total"] == len(a["matched_skills"]) + len(a["not_evidenced_skills"]) + len(a["uncertain_skills"])
    assert a["coverage_score"] == round(a["requirements_matched"] / a["requirements_total"] * 100, 1)
    assert any(s["skill_name"] == "FastAPI" and s["resume_evidence"] for s in a["matched_skills"])
    assert any(s["skill_name"] == "Kubernetes" for s in a["not_evidenced_skills"])
    assert a["recommendations"] and a["created_at"].endswith("Z") or "+00:00" in a["created_at"]
    # reopen later
    again = client.get(f"/api/analyses/{a['id']}").json()
    assert again == a
    with session_factory() as s:
        assert s.scalar(select(func.count()).select_from(SkillMatch)) == a["requirements_total"]


def test_history_listing_search_sort(client):
    make_analysis(client)
    r = upload(client, "r2.docx", make_docx("Python developer who built Docker images and APIs for two years."))
    j = client.post("/api/jobs", json={"title": "Data Engineer", "company_name": "Globex", "description_text": "Experience with Python and Docker required for this role."}).json()
    client.post("/api/analyses", json={"resume_id": r.json()["id"], "job_id": j["id"]})
    body = client.get("/api/analyses").json()
    assert body["total"] == 2 and body["items"][0]["job_title"] == "Data Engineer"  # newest first
    assert client.get("/api/analyses", params={"q": "globex"}).json()["total"] == 1
    top = client.get("/api/analyses", params={"sort_by": "coverage", "order": "desc"}).json()["items"]
    assert top[0]["coverage_score"] >= top[1]["coverage_score"]
    assert client.get("/api/analyses", params={"sort_by": "bogus"}).status_code == 422


def test_delete_analysis_cascades_children_and_orphan_job(client, session_factory):
    _, _, resp = make_analysis(client)
    aid = resp.json()["id"]
    assert client.delete(f"/api/analyses/{aid}").status_code == 204
    assert client.get(f"/api/analyses/{aid}").status_code == 404
    with session_factory() as s:
        for model in (Analysis, SkillMatch, Recommendation, JobDescription):
            assert s.scalar(select(func.count()).select_from(model)) == 0
        assert s.scalar(select(func.count()).select_from(Resume)) == 1  # resume kept


def test_delete_resume_cascades_everything(client, session_factory):
    r, _, resp = make_analysis(client)
    assert client.delete(f"/api/resumes/{r['id']}").status_code == 204
    assert client.get(f"/api/analyses/{resp.json()['id']}").status_code == 404
    with session_factory() as s:
        for model in (Resume, Analysis, SkillMatch, Recommendation, JobDescription):
            assert s.scalar(select(func.count()).select_from(model)) == 0


def test_foreign_keys_enforced(session_factory):
    with session_factory() as s:
        assert s.execute(text("PRAGMA foreign_keys")).scalar() == 1
        s.add(Analysis(resume_id=999, job_id=999, coverage_score=0, semantic_similarity=0, model_version="x"))
        try:
            s.commit()
            raised = False
        except Exception:
            raised = True
        assert raised


def test_openapi_docs_available(client):
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/docs").status_code == 200
