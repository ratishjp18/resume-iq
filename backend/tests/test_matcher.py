from app.services.matcher import extract_requirements, match_resume
from app.services.recommender import recommend
from tests.sample_data import JOB_TEXT, NO_SKILLS_JOB, RESUME_TEXT


def run(resume, job, emb, settings):
    return match_resume(resume, job, emb, settings)


def by_name(outcome):
    return {m.name: m for m in outcome.matches}


def test_requirements_extracted_from_job():
    reqs = extract_requirements(JOB_TEXT)
    names = [r.name for r in reqs]
    for s in ["Python", "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes", "AWS", "Java"]:
        assert s in names
    assert any(r.kind == "statement" and "documentation" in r.name for r in reqs)


def test_statuses_and_coverage_formula(fake_embedder, settings):
    out = run(RESUME_TEXT, JOB_TEXT, fake_embedder, settings)
    m = by_name(out)
    assert m["Python"].status == "matched"
    assert m["FastAPI"].status == "matched" and m["FastAPI"].evidence
    assert m["Docker"].status == "matched"
    assert m["Kubernetes"].status == "not_evidenced"  # explicitly negated in resume
    assert m["AWS"].status == "not_evidenced"
    assert m["Redis"].status != "matched"  # never mentioned
    matched = sum(1 for x in out.matches if x.status == "matched")
    assert out.coverage == round(matched / len(out.matches) * 100, 1)
    assert 0 <= out.semantic_similarity <= 1


def test_unrelated_passage_never_marks_skill_matched(fake_embedder, settings):
    resume = "Managed a team of Redis enthusiasts and worked with databases and caching systems for many years."
    out = run(resume, "Experience with Redis required.", fake_embedder, settings)
    # "Redis" is mentioned -> matched legitimately; now one where it is NOT mentioned:
    out2 = run("Worked extensively with caching systems and in-memory databases for many years.", "Experience with Redis.", fake_embedder, settings)
    assert by_name(out)["Redis"].status == "matched"
    assert by_name(out2)["Redis"].status in ("uncertain", "not_evidenced")


def test_skill_list_only_is_flagged_as_listed(fake_embedder, settings):
    out = run("Skills: Python, Docker, Git, SQL", "Experience with Docker.", fake_embedder, settings)
    d = by_name(out)["Docker"]
    assert d.status == "matched" and d.evidence_strength == "listed"
    recs = [msg for cat, msg in recommend(out.matches, "Skills: Python, Docker, Git, SQL")]
    assert any("Docker" in r and "project" in r for r in recs)


def test_demonstrated_evidence(fake_embedder, settings):
    out = run("Built and deployed microservices using Docker in production for two years.", "Experience with Docker.", fake_embedder, settings)
    assert by_name(out)["Docker"].evidence_strength == "demonstrated"


def test_no_requirements_identified(fake_embedder, settings):
    out = run(RESUME_TEXT, NO_SKILLS_JOB, fake_embedder, settings)
    assert out.total == 0 and out.coverage == 0.0 and out.semantic_similarity == 0.0


def test_empty_resume_passages(fake_embedder, settings):
    out = run("   ", "Experience with Python.", fake_embedder, settings)
    assert out.coverage == 0.0 and out.matches[0].status == "not_evidenced"


def test_all_matched_is_100(fake_embedder, settings):
    out = run("Developed APIs in Python and used Docker for deployment.", "Python and Docker experience.", fake_embedder, settings)
    assert out.coverage == 100.0


def test_recommendations_from_gaps_without_fabrication(fake_embedder, settings):
    out = run(RESUME_TEXT, JOB_TEXT, fake_embedder, settings)
    recs = recommend(out.matches, RESUME_TEXT)
    text = " ".join(m for _, m in recs)
    assert "Consider learning Docker" not in text  # Docker is evidenced
    assert any("AWS" in m and "Explore AWS fundamentals" in m for _, m in recs)
    assert any("Kubernetes" in m for _, m in recs)


def test_sentence_with_several_skills_is_not_treated_as_a_list(fake_embedder, settings):
    text = "Built REST APIs with FastAPI and PostgreSQL serving 20,000 daily requests."
    out = run(text, "Experience with FastAPI.", fake_embedder, settings)
    assert by_name(out)["FastAPI"].evidence_strength == "demonstrated"
