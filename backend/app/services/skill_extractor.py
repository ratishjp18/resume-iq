"""Rule-based, catalog-driven skill extraction with alias handling and negation detection."""
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.services.text_utils import split_passages, truncate

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "skills.json"

# Phrases that, appearing shortly before a skill in the same clause, negate it.
_NEGATION = re.compile(
    r"\b(?:no|zero|little|limited)\s+(?:prior\s+|professional\s+|hands-on\s+|practical\s+|real-world\s+)?"
    r"(?:experience|exposure|knowledge|background|familiarity)\b"
    r"|\bnot\s+(?:familiar|experienced|proficient|comfortable|skilled)\b"
    r"|\bunfamiliar\s+with\b|\binexperienced\s+(?:in|with)\b"
    r"|\b(?:never|haven't|have\s+not|hasn't|has\s+not|didn't|did\s+not)\s+(?:used|worked|touched|tried)\b"
    r"|\b(?:don't|do\s+not|doesn't)\s+(?:have|know|use)\b"
    r"|\bwithout\s+(?:any\s+)?(?:experience|knowledge|using)\b"
    r"|\black(?:s|ing)?\s+(?:of\s+)?(?:experience|knowledge|exposure)?\b",
    re.IGNORECASE,
)
_CLAUSE_BREAK = re.compile(r"[.;:!?\n]|\bbut\b|\bhowever\b|\bthough\b|\balthough\b", re.IGNORECASE)
_NEGATION_WINDOW = 70


@dataclass(frozen=True)
class SkillMention:
    skill: str
    category: str
    snippet: str
    negated: bool
    alias: str


@dataclass(frozen=True)
class _Pattern:
    skill: str
    category: str
    alias: str
    regex: re.Pattern


# "Go" is also an everyday English word, so the bare form only counts in tech-like contexts:
# in a list ("Python, Go, Java"), or right after "in/with/using" ("proficient in Go.").
_GO_CONTEXT = (
    r"(?:(?<![A-Za-z0-9_+#.])Go(?=\s*[,/;)]|\s+(?:language|programming)\b)"
    r"|(?<=[,/(] )Go\b(?![\w-])|(?<=[,/(])Go\b(?![\w-])"
    r"|(?:(?<=in )|(?<=with )|(?<=using ))Go(?=\s*(?:[.,;)]|$|\s(?:and|or)\b)))"
)


def _build_regex(alias: str, case_sensitive: bool) -> re.Pattern:
    if alias == "Go":
        return re.compile(_GO_CONTEXT)
    body = r"\s+".join(re.escape(part) for part in alias.split())
    # Boundaries: not preceded/followed by identifier-ish characters, so "Java" never matches inside
    # "JavaScript", "Go" never matches inside "Google", and "C++"/"C#"/".NET" stay intact.
    pattern = rf"(?<![A-Za-z0-9_+#.]){body}(?![A-Za-z0-9_+#])(?!\.[A-Za-z0-9])"
    return re.compile(pattern, 0 if case_sensitive else re.IGNORECASE)


@lru_cache
def _load_patterns(path: str = str(CATALOG_PATH)) -> tuple[_Pattern, ...]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    case_sensitive = set(data.get("case_sensitive", []))  # ambiguous aliases matched with exact capitalisation only
    patterns: list[_Pattern] = []
    for category, skills in data["categories"].items():
        for skill, aliases in skills.items():
            for alias in {skill, *aliases}:
                patterns.append(_Pattern(skill, category, alias, _build_regex(alias, alias in case_sensitive)))
    # Longest aliases first so overlapping matches resolve to the most specific term.
    patterns.sort(key=lambda p: len(p.alias), reverse=True)
    return tuple(patterns)


def skill_catalog() -> dict[str, str]:
    """Canonical skill -> category."""
    return {p.skill: p.category for p in _load_patterns()}


def _is_negated(text: str, start: int) -> bool:
    window = text[max(0, start - _NEGATION_WINDOW):start]
    breaks = list(_CLAUSE_BREAK.finditer(window))
    if breaks:
        window = window[breaks[-1].end():]
    return bool(_NEGATION.search(window))


def extract_skills(text: str) -> list[SkillMention]:
    """Find every catalog skill mention in `text`, one SkillMention per occurrence (overlaps resolved)."""
    mentions: list[SkillMention] = []
    taken: list[tuple[int, int]] = []
    for pat in _load_patterns():
        for m in pat.regex.finditer(text):
            span = (m.start(), m.end())
            if any(s < span[1] and span[0] < e for s, e in taken):
                continue
            taken.append(span)
            mentions.append(
                SkillMention(pat.skill, pat.category, truncate(_context(text, m.start(), m.end())), _is_negated(text, m.start()), m.group(0))
            )
    return mentions


def _context(text: str, start: int, end: int) -> str:
    """The sentence/line surrounding a match."""
    left = max(text.rfind("\n", 0, start), text.rfind(". ", 0, start))
    right_candidates = [i for i in (text.find("\n", end), text.find(". ", end)) if i != -1]
    right = min(right_candidates) if right_candidates else len(text)
    return text[left + 1 if left != -1 else 0: right + 1].strip(" \n.•-*")


def unique_skills(mentions: list[SkillMention], include_negated: bool = False) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in mentions:
        if m.negated and not include_negated:
            continue
        out.setdefault(m.skill, m.category)
    return out


def extract_from_passages(text: str) -> list[tuple[str, list[SkillMention]]]:
    """Extract skills per passage (sentence/bullet); returns [(passage, mentions)] for passages with hits."""
    return [(p, ms) for p in split_passages(text, min_words=1) if (ms := extract_skills(p))]
