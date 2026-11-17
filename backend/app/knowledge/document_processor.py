"""Sanitising and chunking educational documents. Standard library only."""
from __future__ import annotations

import re

MAX_DOC_CHARS = 200_000
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\u200b-\u200f\u202a-\u202e\u2060\ufeff]")
_TAGS = re.compile(r"<\s*/?\s*(?:script|style|iframe|object|embed|reference_material|user_profile|system)[^>]*>", re.I)
_INJECTION = re.compile(
    r"(ignore\s+(?:all\s+|any\s+)?(?:previous|prior|above)\s+(?:instructions|rules)|disregard\s+(?:the\s+)?"
    r"(?:system|previous)|you\s+are\s+now\s+|reveal\s+(?:your\s+)?(?:system\s+)?prompt|"
    r"new\s+instructions\s*:|act\s+as\s+(?:an?\s+)?(?:unrestricted|jailbroken))", re.I)


def sanitize_document(text: str) -> str:
    if len(text) > MAX_DOC_CHARS:
        raise ValueError("document is too large")
    t = _CTRL.sub("", text)
    t = _TAGS.sub("", t)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def find_injection(text: str) -> list:
    return [m.group(0)[:80] for m in _INJECTION.finditer(text)]


def chunk_text(text: str, size: int = 900, overlap: int = 120) -> list:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks, cur = [], ""
    for p in paras:
        while len(p) > size:  # split oversized paragraphs on sentence/space boundaries
            cut = max(p.rfind(". ", 0, size), p.rfind(" ", 0, size))
            cut = cut + 1 if cut > size // 2 else size
            if cur:
                chunks.append(cur); cur = ""
            chunks.append(p[:cut].strip()); p = p[max(cut - overlap, 1):].strip() if len(p) > cut else ""
        if not p:
            continue
        if cur and len(cur) + len(p) + 2 > size:
            chunks.append(cur)
            cur = (cur[-overlap:] + "\n\n" + p) if overlap and len(cur) > overlap else p
        else:
            cur = f"{cur}\n\n{p}" if cur else p
    if cur:
        chunks.append(cur)
    return [c for c in chunks if c.strip()]
