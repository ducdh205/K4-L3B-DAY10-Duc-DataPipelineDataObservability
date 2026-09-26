from __future__ import annotations

import hashlib
import re

import numpy as np
from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


class MiniLMEmbeddings(Embeddings):
    """Sentence-Transformers MiniLM adapter with a deterministic offline fallback."""
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.backend = "sentence-transformers"
        self._model = None

    @staticmethod
    def _embed(text: str) -> list[float]:
        vector = np.zeros(384, dtype=np.float32)
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            vector[int.from_bytes(digest[:2], "big") % 384] += 1 if digest[2] % 2 else -1
        norm = np.linalg.norm(vector)
        return (vector / norm if norm else vector).tolist()

    def _encode(self, texts: list[str]) -> list[list[float]]:
        try:
            if self._model is None:
                self._model = SentenceTransformer(self.model_name)
            vectors = self._model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(vectors, dtype=np.float32).tolist()
        except Exception:
            self.backend = "deterministic-hash-fallback"
            return [self._embed(text) for text in texts]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text])[0]
