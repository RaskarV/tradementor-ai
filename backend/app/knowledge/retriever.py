import logging

from sqlalchemy import select

from app.database.models import KnowledgeChunk, KnowledgeDocument
from app.knowledge.document_processor import chunk_text, sanitize_document
from app.knowledge.embeddings import EmbeddingProvider
from app.knowledge.types import Retrieved

log = logging.getLogger(__name__)


class Retriever:
    def __init__(self, embedder_getter, k: int = 4):
        self._get_embedder, self._k = embedder_getter, k

    async def search(self, session, query: str) -> list:
        if session is None or not query.strip():
            return []
        vec = (await self._get_embedder().embed([query], "query"))[0]
        dist = KnowledgeChunk.embedding.cosine_distance(vec)
        rows = (await session.execute(
            select(KnowledgeChunk.content, KnowledgeDocument.title, KnowledgeDocument.source_url, dist)
            .join(KnowledgeDocument, KnowledgeDocument.id == KnowledgeChunk.document_id)
            .where(KnowledgeDocument.is_published.is_(True)).order_by(dist).limit(self._k))).all()
        return [Retrieved(title, url, content, 1.0 - float(d)) for content, title, url, d in rows]

    async def index_document(self, session, doc: KnowledgeDocument) -> int:
        chunks = chunk_text(sanitize_document(doc.body))
        vectors = await self._get_embedder().embed(chunks, "document") if chunks else []
        await session.execute(KnowledgeChunk.__table__.delete().where(KnowledgeChunk.document_id == doc.id))
        for i, (c, v) in enumerate(zip(chunks, vectors)):
            session.add(KnowledgeChunk(document_id=doc.id, chunk_index=i, content=c, embedding=v))
        await session.flush()
        return len(chunks)
