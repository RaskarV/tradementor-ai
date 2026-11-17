"""Load the starter curriculum and build embeddings.  Usage: python -m scripts.seed_knowledge
Safe to re-run: documents are matched by title and re-indexed."""
import asyncio

from sqlalchemy import select

from app.config import get_settings
from app.database.models import KnowledgeDocument
from app.database.session import SessionLocal
from app.knowledge.embeddings import get_embedder
from app.knowledge.retriever import Retriever
from app.knowledge.seed_content import SEED_DOCS
from app.knowledge.topics import TOPICS


async def main():
    titles = dict(TOPICS)
    retriever = Retriever(lambda: get_embedder(get_settings()))
    async with SessionLocal() as s:
        for slug, body in SEED_DOCS.items():
            title = titles[slug]
            doc = await s.scalar(select(KnowledgeDocument).where(KnowledgeDocument.title == title))
            if doc is None:
                doc = KnowledgeDocument(title=title, topic=slug, body=body)
                s.add(doc)
            else:
                doc.body = body
            await s.flush()
            n = await retriever.index_document(s, doc)
            print(f"{title}: {n} chunk(s)")
        await s.commit()


asyncio.run(main())
