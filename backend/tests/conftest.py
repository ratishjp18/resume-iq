import io
import re

import numpy as np
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.database import Base, get_db, make_engine
from app.main import create_app
from app.services import embedding
from app.services.text_utils import content_tokens


class FakeEmbedder:
    """Deterministic hashed bag-of-words embedder; keeps unit tests fast and offline."""

    model_name = "fake-embedder"
    dim = 512

    def encode(self, texts):
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, t in enumerate(texts):
            for tok in content_tokens(t) | set(re.findall(r"[a-z0-9+#]+", t.lower())):
                out[i, hash(tok) % self.dim] += 1.0
        norms = np.linalg.norm(out, axis=1, keepdims=True)
        return out / np.where(norms == 0, 1, norms)


@pytest.fixture()
def settings():
    return get_settings()


@pytest.fixture()
def fake_embedder():
    return FakeEmbedder()


@pytest.fixture()
def session_factory():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def db(session_factory):
    s = session_factory()
    yield s
    s.close()


@pytest.fixture()
def client(session_factory, fake_embedder):
    app = create_app()

    def _db():
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[embedding.get_embedder] = lambda: fake_embedder
    return TestClient(app)


def make_pdf(text: str) -> bytes:
    import pymupdf as fitz

    doc = fitz.open()
    lines = text.split("\n")
    for start in range(0, len(lines), 45):
        page = doc.new_page()
        y = 60
        for line in lines[start:start + 45]:
            page.insert_text((50, y), line, fontsize=10)
            y += 14
    data = doc.tobytes()
    doc.close()
    return data


def make_blank_pdf() -> bytes:
    import pymupdf as fitz

    doc = fitz.open()
    doc.new_page()
    data = doc.tobytes()
    doc.close()
    return data


def make_docx(text: str) -> bytes:
    from docx import Document

    d = Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    buf = io.BytesIO()
    d.save(buf)
    return buf.getvalue()
