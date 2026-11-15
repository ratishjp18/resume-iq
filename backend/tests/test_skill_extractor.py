import pytest

from app.services.skill_extractor import extract_skills, skill_catalog, unique_skills


def skills(text, include_negated=False):
    return set(unique_skills(extract_skills(text), include_negated))


def test_catalog_has_required_categories_and_skills():
    cat = skill_catalog()
    for s in ["Python", "Java", "JavaScript", "TypeScript", "Go", "C#", "SQL", "React", "Angular", "Vue", "FastAPI",
              "Django", "Flask", "Spring Boot", "Node.js", "Express", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Docker",
              "Kubernetes", "AWS", "Azure", "GCP", "Git", "REST APIs", "TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy"]:
        assert s in cat, s
    assert {"Programming Languages", "Databases", "Cloud Platforms", "DevOps", "AI/ML", "Testing", "Version Control"} <= set(cat.values())


@pytest.mark.parametrize("text,expected", [
    ("React.js and ReactJS", {"React"}),
    ("Wrote JS and TS code", {"JavaScript", "TypeScript"}),
    ("Used Postgres daily", {"PostgreSQL"}),
    ("Built services in Node and Golang", {"Node.js", "Go"}),
    ("Deployed on Amazon Web Services", {"AWS"}),
    ("Experience with C++ and C#", {"C++", "C#"}),
    ("Built with ASP.NET and Node.js", {"ASP.NET", "Node.js"}),
    ("Used scikit-learn, NumPy and Pandas", {"Scikit-learn", "NumPy", "Pandas"}),
    ("Designed RESTful APIs", {"REST APIs"}),
    ("Used k8s and CI/CD", {"Kubernetes", "CI/CD"}),
])
def test_aliases(text, expected):
    assert skills(text) == expected


@pytest.mark.parametrize("text,absent", [
    ("Strong JavaScript skills", "Java"),
    ("I work at Google on search", "Go"),
    ("Please go to the next page and Go home", "Go"),
    ("Rest of the team was great", "REST APIs"),
    ("The Pythonic way", "Python"),
    ("I enjoy the Reactor pattern", "React"),
    ("Familiar with MongoDB", "SQL"),
    ("Studied at Springfield college in Spring", "Spring Boot"),
])
def test_no_false_substring_matches(text, absent):
    assert absent not in skills(text)


def test_javascript_does_not_imply_java_but_both_can_coexist():
    assert skills("JavaScript") == {"JavaScript"}
    assert skills("Java and JavaScript") == {"Java", "JavaScript"}


def test_negation_detected():
    ms = extract_skills("I have no experience with Kubernetes. I used Docker daily.")
    by = {m.skill: m for m in ms}
    assert by["Kubernetes"].negated is True
    assert by["Docker"].negated is False
    assert "Kubernetes" not in skills("I have no experience with Kubernetes.")
    assert "Kubernetes" in skills("I have no experience with Kubernetes.", include_negated=True)


def test_negation_does_not_leak_across_clauses():
    ms = {m.skill: m for m in extract_skills("Not familiar with Java, but I built APIs in Python.")}
    assert ms["Java"].negated and not ms["Python"].negated


def test_evidence_snippet_contains_context():
    m = extract_skills("Intro line.\nBuilt REST APIs with FastAPI for billing.\nOther.")
    fast = next(x for x in m if x.skill == "FastAPI")
    assert "billing" in fast.snippet and "Intro" not in fast.snippet
