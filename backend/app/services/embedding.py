"""Sentence Transformers embedding service. The model is loaded once per process and cached on disk."""
import logging
import threading
from typing import Protocol

import numpy as np

from app.config import get_settings

logger = logging.getLogger("resumeiq.embedding")


class Embedder(Protocol):
    model_name: str

    def encode(self, texts: list[str]) -> np.ndarray:
        """Return an (n, d) array of L2-normalised embeddings."""
        ...


class SentenceTransformerEmbedder:
    def __init__(self, model_name: str, cache_dir: str):
        from sentence_transformers import SentenceTransformer

        logger.info("Loading embedding model %s (first run downloads it to %s)", model_name, cache_dir)
        self.model_name = model_name
        self._model = SentenceTransformer(model_name, cache_folder=cache_dir, device="cpu")
        self._lock = threading.Lock()

    def encode(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self._model.get_sentence_embedding_dimension()), dtype=np.float32)
        with self._lock:
            vecs = self._model.encode(
                texts, batch_size=32, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
            )
        return np.asarray(vecs, dtype=np.float32)


_embedder: Embedder | None = None
_load_lock = threading.Lock()


def get_embedder() -> Embedder:
    """Process-wide singleton (also used as a FastAPI dependency so tests can override it)."""
    global _embedder
    if _embedder is None:
        with _load_lock:
            if _embedder is None:
                s = get_settings()
                _embedder = SentenceTransformerEmbedder(s.embedding_model, s.model_cache_dir)
    return _embedder
