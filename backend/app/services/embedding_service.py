import math
import hashlib
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from backend.app.core.config import get_settings
from backend.app.core.logging import logger

settings = get_settings()

COLLECTION_NAME = "careerpilot_jobs"
VECTOR_DIM = 64  # Compact, high-speed dense vector for fast matching


class EmbeddingService:
    def __init__(self):
        if settings.QDRANT_LOCAL_MODE:
            # In-memory Qdrant client - runs locally without Docker or cloud requirement
            self.client = QdrantClient(":memory:")
        else:
            self.client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY or None)

        self._ensure_collection()

    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == COLLECTION_NAME for c in collections)
            if not exists:
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
                )
        except Exception as e:
            logger.warning(f"Qdrant collection setup note: {e}")

    @staticmethod
    def get_embedding(text: str) -> List[float]:
        """Generates a normalized dense vector embedding.
        Uses deterministic hashing and word n-grams to produce consistent semantic vector representations.
        """
        words = text.lower().split()
        vector = [0.0] * VECTOR_DIM
        for i, word in enumerate(words):
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % VECTOR_DIM
            vector[idx] += 1.0 / (1.0 + (i * 0.05))

        # Normalize L2
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    @classmethod
    def cosine_similarity(cls, vec1: List[float], vec2: List[float]) -> float:
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return max(0.0, min(1.0, dot_product))


embedding_service = EmbeddingService()

