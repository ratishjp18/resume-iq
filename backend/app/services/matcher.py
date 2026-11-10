"""Semantic + explicit-skill matching and scoring.

Method (see docs/architecture.md):
  1. Job requirements = every non-negated catalog skill in the job description (type "skill") plus requirement
     statements that contain no catalog skill (type "statement").
  2. Resume text is split into sentence/bullet passages; requirements and passages are embedded locally.
  3. Skill requirements: an explicit, non-negated mention of the skill is required for "matched". Embeddings pick the
     best supporting passage. Without an explicit mention the best outcome is "uncertain" (related-skill or purely
     semantic evidence that needs human review) - never "matched".
  4. Statement requirements: matched only if cosine similarity >= threshold AND the passage shares at least one content
     word with the requirement; otherwise uncertain / not evidenced.
Thresholds are unvalidated defaults and must be tuned against labeled examples.
"""
import re
from dataclasses import dataclass, field

import numpy as np

from app.config import Settings
from app.services.embedding import Embedder
from app.services.skill_extractor import SkillMention, extract_skills
from app.services.text_utils import content_tokens, split_passages, truncate

MATCHER_VERSION = "matcher-v1"
MAX_STATEMENTS = 12

_REQUIREMENT_CUES = re.compile(
    r"\b(experience|experienced|ability|able to|knowledge|proficien\w*|familiar\w*|understanding|expertise|skilled|"
    r"demonstrated|proven|years|degree|must have|required)\b",
    re.IGNORECASE,
)
_LIST_LABEL = re.compile(r"^\s*(?:technical\s+)?(?:skills|technologies|tools|languages|frameworks|tech stack)\b", re.IGNORECASE)


@dataclass
class Requirement:
    name: str
    kind: str  # "skill" | "statement"
    category: str
    query: str


@dataclass
class MatchResult:
    name: str
    status: str  # matched | not_evidenced | uncertain
    category: str
    requirement_type: str
    similarity: float | None
    evidence: str | None = None
    evidence_strength: str | None = None  # demonstrated | listed (skills only)
    note: str | None = None


@dataclass
class AnalysisOutcome:
    coverage: float
    semantic_similarity: float
    matches: list[MatchResult] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.matches)


def extract_requirements(job_text: str) -> list[Requirement]:
    reqs: list[Requirement] = []
    seen: set[str] = set()
    statements = 0
    for passage in split_passages(job_text, min_words=1):
        mentions = extract_skills(passage)
        for m in mentions:
            if m.negated or m.skill in seen:
                continue
            seen.add(m.skill)
            reqs.append(Requirement(m.skill, "skill", m.category, f"Experience with {m.skill}"))
        if not mentions and statements < MAX_STATEMENTS and len(passage.split()) >= 4 and _REQUIREMENT_CUES.search(passage):
            text = truncate(passage, 200)
            if text.lower() not in seen:
                seen.add(text.lower())
                reqs.append(Requirement(text, "statement", "General", text))
                statements += 1
    return reqs


def _is_listy(passage: str, n_skills: int) -> bool:
    words = len(passage.split())
    # A bare list ("Docker, Git, SQL") is dense with skills; a sentence describing work is not.
    return bool(_LIST_LABEL.match(passage)) or words < 5 or n_skills / words >= 0.3


def match_resume(resume_text: str, job_text: str, embedder: Embedder, settings: Settings) -> AnalysisOutcome:
    reqs = extract_requirements(job_text)
    if not reqs:
        return AnalysisOutcome(coverage=0.0, semantic_similarity=0.0, matches=[])

    passages = split_passages(resume_text, min_words=1)
    if not passages:
        matches = [MatchResult(r.name, "not_evidenced", r.category, r.kind, None) for r in reqs]
        return AnalysisOutcome(0.0, 0.0, matches)

    req_vecs = embedder.encode([r.query for r in reqs])
    pas_vecs = embedder.encode(passages)
    sims = np.clip(req_vecs @ pas_vecs.T, -1.0, 1.0)  # cosine: both sides are L2-normalised

    # Index resume skill mentions by passage.
    passage_mentions: list[list[SkillMention]] = [extract_skills(p) for p in passages]
    by_skill: dict[str, list[tuple[int, bool]]] = {}
    for idx, ms in enumerate(passage_mentions):
        for m in ms:
            by_skill.setdefault(m.skill, []).append((idx, m.negated))
    long_enough = np.array([len(p.split()) >= 4 for p in passages])

    results: list[MatchResult] = []
    best_overall: list[float] = []
    for i, req in enumerate(reqs):
        row = sims[i]
        best_overall.append(float(row.max()))
        if req.kind == "skill":
            results.append(_match_skill(req, row, passages, passage_mentions, by_skill, long_enough, settings))
        else:
            results.append(_match_statement(req, row, passages, long_enough, settings))

    matched = sum(1 for r in results if r.status == "matched")
    coverage = round(matched / len(results) * 100, 1)
    semantic = round(float(np.clip(np.mean(best_overall), 0.0, 1.0)), 4)
    return AnalysisOutcome(coverage, semantic, results)


def _match_skill(req, row, passages, passage_mentions, by_skill, long_enough, s: Settings) -> MatchResult:
    hits = by_skill.get(req.name, [])
    positive = [idx for idx, neg in hits if not neg]
    negative = [idx for idx, neg in hits if neg]

    if positive:
        # Prefer passages describing actual use over bare skill lists, then the highest cosine similarity.
        def rank(idx: int):
            listy = _is_listy(passages[idx], len(passage_mentions[idx]))
            return (not listy, float(row[idx]))

        best = max(positive, key=rank)
        demonstrated = any(not _is_listy(passages[i], len(passage_mentions[i])) for i in positive)
        return MatchResult(
            req.name, "matched", req.category, "skill", round(float(row[best]), 4), truncate(passages[best]),
            "demonstrated" if demonstrated else "listed",
            None if demonstrated else "Mentioned only in a skills list or very short line; no supporting context found.",
        )

    if negative:
        best = max(negative, key=lambda i: float(row[i]))
        return MatchResult(
            req.name, "not_evidenced", req.category, "skill", round(float(row[best]), 4), truncate(passages[best]),
            None, "The resume contains a statement that appears to say this skill is limited or absent.",
        )

    # No explicit mention: related same-category skills or purely semantic hints can only yield "uncertain".
    related = [
        i for i, ms in enumerate(passage_mentions)
        if any(m.category == req.category and m.skill != req.name and not m.negated for m in ms)
    ]
    if related:
        best = max(related, key=lambda i: float(row[i]))
        if row[best] >= s.threshold_related_skill:
            skills = sorted({m.skill for m in passage_mentions[best] if m.category == req.category and not m.negated})
            return MatchResult(
                req.name, "uncertain", req.category, "skill", round(float(row[best]), 4), truncate(passages[best]),
                None, f"{req.name} is not mentioned, but related {req.category.lower()} experience was found ({', '.join(skills)}). Review manually.",
            )

    best = int(np.argmax(np.where(long_enough, row, -1.0))) if long_enough.any() else int(np.argmax(row))
    if row[best] >= s.threshold_semantic_only_skill:
        return MatchResult(
            req.name, "uncertain", req.category, "skill", round(float(row[best]), 4), truncate(passages[best]),
            None, f"{req.name} is not mentioned; the closest passage is only semantically related. Review manually.",
        )
    return MatchResult(req.name, "not_evidenced", req.category, "skill", round(float(row[best]), 4), None)


def _match_statement(req: Requirement, row, passages, long_enough, s: Settings) -> MatchResult:
    masked = np.where(long_enough, row, -1.0) if long_enough.any() else row
    best = int(np.argmax(masked))
    sim = float(row[best])
    overlap = bool(content_tokens(req.query) & content_tokens(passages[best]))
    if sim >= s.threshold_semantic_match and overlap:
        status, note = "matched", None
    elif sim >= s.threshold_semantic_match:
        status, note = "uncertain", "High semantic similarity but no shared key terms; review manually."
    elif sim >= s.threshold_semantic_uncertain:
        status, note = "uncertain", "Partially related passage found; review manually."
    else:
        return MatchResult(req.name, "not_evidenced", req.category, "statement", round(sim, 4), None)
    return MatchResult(req.name, status, req.category, "statement", round(sim, 4), truncate(passages[best]), None, note)
