"""Document upload / ingestion endpoints."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..intelligence.knowledge.service import get_knowledge_base
from ..models import Chunk, Document, Organisation
from ..schemas import DocumentRead

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf", ".docx", ".csv", ".json"}


@router.post("/upload", response_model=DocumentRead, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    organisation_id: int | None = Form(None),
    title: str = Form(""),
    industry: str = Form(""),
    source: str = Form(""),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(400, "No file provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(400, f"File exceeds {settings.max_upload_mb} MB limit")

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / file.filename
    dest.write_bytes(content)

    # Ingest into the knowledge base (extract -> chunk -> embed -> store).
    kb = get_knowledge_base()
    kb.ensure_seeded()
    chunk_ids = kb.ingest_file(dest, source=source, title=title, industry=industry)

    doc = Document(
        organisation_id=organisation_id,
        filename=file.filename,
        title=title or Path(file.filename).stem,
        source=source,
        industry=industry,
        content_type=ext,
    )
    db.add(doc)
    db.flush()
    for cid in chunk_ids:
        db.add(Chunk(document_id=doc.id, text=cid, section="", meta={"chunk_id": cid}))
    db.commit()
    db.refresh(doc)
    return doc
