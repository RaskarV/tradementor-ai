from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingError(Exception):
    pass


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: list, kind: str = "document") -> list:
        """kind: 'document' or 'query'. Returns one vector per text."""


class VoyageEmbeddings(EmbeddingProvider):
    def __init__(self, api_key: str, model: str, dim: int):
        if not api_key:
            raise EmbeddingError("VOYAGE_API_KEY is not configured")
        self._key, self._model, self._dim = api_key, model, dim

    async def embed(self, texts, kind="document"):
        import httpx
        out: list = []
        async with httpx.AsyncClient(timeout=30) as c:
            for i in range(0, len(texts), 64):
                r = await c.post("https://api.voyageai.com/v1/embeddings",
                                 headers={"Authorization": f"Bearer {self._key}"},
                                 json={"input": texts[i:i + 64], "model": self._model, "input_type": kind,
                                       "output_dimension": self._dim})
                if r.status_code >= 400:
                    raise EmbeddingError(f"voyage error {r.status_code}")
                out += [d["embedding"] for d in r.json()["data"]]
        return out


class OpenAIEmbeddings(EmbeddingProvider):
    def __init__(self, api_key: str, model: str, dim: int):
        if not api_key:
            raise EmbeddingError("OPENAI_API_KEY is not configured")
        self._key, self._model, self._dim = api_key, model, dim

    async def embed(self, texts, kind="document"):
        import httpx
        out: list = []
        async with httpx.AsyncClient(timeout=30) as c:
            for i in range(0, len(texts), 96):
                r = await c.post("https://api.openai.com/v1/embeddings",
                                 headers={"Authorization": f"Bearer {self._key}"},
                                 json={"input": texts[i:i + 96], "model": self._model, "dimensions": self._dim})
                if r.status_code >= 400:
                    raise EmbeddingError(f"openai embeddings error {r.status_code}")
                out += [d["embedding"] for d in r.json()["data"]]
        return out


def get_embedder(settings) -> EmbeddingProvider:
    if settings.embedding_provider == "voyage":
        return VoyageEmbeddings(settings.voyage_api_key, settings.embedding_model or "voyage-3", settings.embedding_dim)
    if settings.embedding_provider == "openai":
        return OpenAIEmbeddings(settings.openai_api_key, settings.embedding_model or "text-embedding-3-small",
                                settings.embedding_dim)
    raise EmbeddingError(f"unknown embedding provider: {settings.embedding_provider}")
