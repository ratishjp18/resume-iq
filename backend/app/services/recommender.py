"""Deterministic, rule-based recommendations from a curated catalog. No generative model, no fabricated experience."""
import json
import re
from pathlib import Path

from app.services.matcher import MatchResult
from app.services.text_utils import truncate

_CATALOG = json.loads((Path(__file__).resolve().parent.parent / "data" / "recommendations.json").read_text(encoding="utf-8"))

MAX_SKILL_GAPS = 8
MAX_EVIDENCE = 5
MAX_STATEMENTS = 3


def _skill_message(skill: str, category: str) -> str:
    specific = _CATALOG["skills"].get(skill)
    if specific:
        return specific
    template = _CATALOG["category_templates"].get(category, _CATALOG["category_templates"]["General"])
    return template.format(skill=skill)


def recommend(matches: list[MatchResult], resume_text: str) -> list[tuple[str, str]]:
    recs: list[tuple[str, str]] = []

    gaps = [m for m in matches if m.requirement_type == "skill" and m.status == "not_evidenced"]
    for m in gaps[:MAX_SKILL_GAPS]:
        recs.append(("skill_gap", f"{m.name} is not evidenced in your resume. {_skill_message(m.name, m.category)}"))

    for m in (m for m in matches if m.requirement_type == "skill" and m.status == "uncertain"):
        recs.append((
            "review",
            f"{m.name}: related experience may exist but it is not stated. If you have genuinely used {m.name}, "
            f"mention it explicitly; if not, {_skill_message(m.name, m.category)[0].lower()}{_skill_message(m.name, m.category)[1:]}",
        ))

    listed = [m for m in matches if m.status == "matched" and m.evidence_strength == "listed"]
    for m in listed[:MAX_EVIDENCE]:
        recs.append((
            "evidence",
            f"{m.name} appears only in a skills list. Consider describing an existing {m.name} project with its "
            "responsibilities and outcomes.",
        ))

    statements = [m for m in matches if m.requirement_type == "statement" and m.status in ("not_evidenced", "uncertain")]
    for m in statements[:MAX_STATEMENTS]:
        recs.append((
            "requirement",
            f"The posting asks: “{truncate(m.name, 140)}”. If you have relevant experience, address it explicitly "
            "in your resume; otherwise treat it as an area to develop.",
        ))

    recs.extend(_general_tips(resume_text))
    return recs


def _general_tips(resume_text: str) -> list[tuple[str, str]]:
    tips: list[tuple[str, str]] = []
    words = len(resume_text.split())
    if words < 150:
        tips.append(("resume_improvement", "Your resume is quite short. Consider adding concise descriptions of your projects, responsibilities and results, where they are true."))
    if not re.search(r"\d", resume_text):
        tips.append(("resume_improvement", "No numbers were found. Where accurate, add measurable outcomes (for example scale, time saved or users served)."))
    if not re.search(r"\b(projects?|experience|employment|work history)\b", resume_text, re.IGNORECASE):
        tips.append(("resume_improvement", "No clear 'Experience' or 'Projects' section was detected. Clearly labelled sections make evidence easier to find."))
    return tips
