import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_db, require
from app.database.models import AuditLog, KnowledgeChunk, KnowledgeDocument
from app.knowledge.document_processor import find_injection, sanitize_document
from app.knowledge.topics import TOPICS

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/knowledge", tags=["knowledge"], dependencies=[Depends(require("admin"))])
_SLUGS = {s for s, _ in TOPICS}


class DocIn(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    topic: str = Field(max_length=64)
    body: str = Field(min_length=20, max_length=200_000)
    source_url: str | None = Field(None, max_length=512, pattern=r"^https?://")
    is_published: bool = True


def _clean(body: str) -> str:
    clean = sanitize_document(body)
    flagged = find_injection(clean)
    if flagged:
        raise HTTPException(422, {"error": "document contains instruction-like text", "matches": flagged})
    return clean


async def _index(request, db, doc):
    try:
        return await request.app.state.retriever.index_document(db, doc)
    except Exception as e:
        await db.rollback()
        log.exception("indexing failed")
        raise HTTPException(502, f"embedding failed: {type(e).__name__}")


@router.get("")
async def list_docs(db: AsyncSession = Depends(get_db)):
    counts = dict((await db.execute(select(KnowledgeChunk.document_id, func.count()).group_by(
        KnowledgeChunk.document_id))).all())
    return [{"id": d.id, "title": d.title, "topic": d.topic, "source_url": d.source_url,
             "is_published": d.is_published, "chunks": counts.get(d.id, 0), "updated_at": d.updated_at}
            for d in (await db.scalars(select(KnowledgeDocument).order_by(KnowledgeDocument.id.desc()))).all()]


@router.get("/{doc_id}")
async def get_doc(doc_id: int, db: AsyncSession = Depends(get_db)):
    d = await db.get(KnowledgeDocument, doc_id)
    if not d:
        raise HTTPException(404, "not found")
    return {"id": d.id, "title": d.title, "topic": d.topic, "source_url": d.source_url, "body": d.body,
            "is_published": d.is_published}


@router.post("", status_code=201)
async def create_doc(body: DocIn, request: Request, db: AsyncSession = Depends(get_db), admin=Depends(require("admin"))):
    doc = KnowledgeDocument(title=body.title, topic=body.topic, body=_clean(body.body), source_url=body.source_url,
                            is_published=body.is_published)
    db.add(doc)
    await db.flush()
    n = await _index(request, db, doc)
    db.add(AuditLog(admin_id=admin.id, action="knowledge_create", target=str(doc.id)))
    await db.commit()
    return {"id": doc.id, "chunks": n}


@router.post("/upload", status_code=201)
async def upload_doc(request: Request, file: UploadFile = File(...), title: str = Form(...), topic: str = Form(...),
                     source_url: str | None = Form(None), db: AsyncSession = Depends(get_db),
                     admin=Depends(require("admin"))):
    if not (file.filename or "").lower().endswith((".txt", ".md")):
        raise HTTPException(415, "only .txt and .md files are accepted")
    raw = await file.read(200_001)
    if len(raw) > 200_000:
        raise HTTPException(413, "file too large")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(422, "file must be UTF-8 text")
    return await create_doc(DocIn(title=title, topic=topic, body=text, source_url=source_url or None), request, db, admin)


@router.put("/{doc_id}")
async def update_doc(doc_id: int, body: DocIn, request: Request, db: AsyncSession = Depends(get_db),
                     admin=Depends(require("admin"))):
    d = await db.get(KnowledgeDocument, doc_id)
    if not d:
        raise HTTPException(404, "not found")
    d.title, d.topic, d.body, d.source_url, d.is_published = body.title, body.topic, _clean(body.body), \
        body.source_url, body.is_published
    n = await _index(request, db, d)
    db.add(AuditLog(admin_id=admin.id, action="knowledge_update", target=str(doc_id)))
    await db.commit()
    return {"id": d.id, "chunks": n}


@router.delete("/{doc_id}")
async def delete_doc(doc_id: int, db: AsyncSession = Depends(get_db), admin=Depends(require("admin"))):
    d = await db.get(KnowledgeDocument, doc_id)
    if not d:
        raise HTTPException(404, "not found")
    await db.delete(d)
    db.add(AuditLog(admin_id=admin.id, action="knowledge_delete", target=str(doc_id)))
    await db.commit()
    return {"ok": True}


@router.post("/rebuild")
async def rebuild(request: Request, db: AsyncSession = Depends(get_db), admin=Depends(require("admin"))):
    total = 0
    for d in (await db.scalars(select(KnowledgeDocument))).all():
        total += await _index(request, db, d)
    db.add(AuditLog(admin_id=admin.id, action="knowledge_rebuild"))
    await db.commit()
    return {"chunks": total}
