"""Runs the REAL sentence-transformers/all-MiniLM-L6-v2 model on CPU. Deselected by default (downloads ~90 MB once).

Run with:  pytest -m integration
"""
import numpy as np
import pytest

from app.config import get_settings
from app.services.embedding import get_embedder
from app.services.matcher import match_resume
from tests.sample_data import JOB_TEXT, RESUME_TEXT

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def embedder():
    return get_embedder()


def test_embeddings_are_real_and_normalised(embedder):
    v = embedder.encode(["Built REST APIs with FastAPI", "Developed web services in Python", "Baking sourdough bread"])
    assert v.shape == (3, 384)
    assert np.allclose(np.linalg.norm(v, axis=1), 1.0, atol=1e-3)
    related, unrelated = float(v[0] @ v[1]), float(v[0] @ v[2])
    assert related > unrelated + 0.15


def test_real_end_to_end_matching(embedder):
    out = match_resume(RESUME_TEXT, JOB_TEXT, embedder, get_settings())
    m = {x.name: x for x in out.matches}
    assert m["FastAPI"].status == "matched" and m["Python"].status == "matched"
    assert m["Kubernetes"].status == "not_evidenced"
    assert m["AWS"].status != "matched"
    assert all(x.similarity is not None for x in out.matches)
    assert 0.0 < out.semantic_similarity < 1.0
    assert 0.0 < out.coverage < 100.0
