from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.knowledge_chunks import KnowledgeChunk
from app.models.saas import RAGIngestionJob
from app.schemas.knowledge import (
    KnowledgeChunkRead,
    KnowledgeCreate,
    KnowledgeIngestRequest,
    KnowledgeIngestResponse,
    KnowledgeRead,
    KnowledgeSearchRequest,
)
from app.services.knowledge import KnowledgeService
from app.services.tenancy import TenantService

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def to_knowledge_read(item) -> KnowledgeRead:
    return KnowledgeRead(
        id=item.id,
        title=item.title,
        body=item.body,
        source=item.source,
        metadata=item.item_metadata,
    )


def to_chunk_read(chunk: KnowledgeChunk) -> KnowledgeChunkRead:
    return KnowledgeChunkRead(
        id=chunk.id,
        organization_id=chunk.organization_id,
        knowledge_id=chunk.knowledge_id,
        chunk_index=chunk.chunk_index,
        body=chunk.body,
        source=chunk.source,
        metadata=chunk.chunk_metadata,
    )


@router.get("/chunks", response_model=list[KnowledgeChunkRead])
def list_chunks(
    organization_id: int | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[KnowledgeChunkRead]:
    context = TenantService(db).resolve(organization_id)
    statement = (
        select(KnowledgeChunk)
        .where(KnowledgeChunk.organization_id == context.organization_id)
        .order_by(KnowledgeChunk.created_at.desc())
        .limit(min(limit, 500))
    )
    return [to_chunk_read(chunk) for chunk in db.scalars(statement)]


@router.post("", response_model=KnowledgeRead, status_code=201)
def create_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db)) -> KnowledgeRead:
    item = KnowledgeService(db).create(payload)
    db.commit()
    db.refresh(item)
    return to_knowledge_read(item)


@router.post("/search", response_model=list[KnowledgeRead])
def search_knowledge(payload: KnowledgeSearchRequest, db: Session = Depends(get_db)) -> list[KnowledgeRead]:
    context = TenantService(db).resolve(payload.organization_id)
    return [to_knowledge_read(item) for item in KnowledgeService(db, context).search(payload.query, payload.limit)]


@router.post("/ingest", response_model=KnowledgeIngestResponse)
def ingest_knowledge(payload: KnowledgeIngestRequest, db: Session = Depends(get_db)) -> KnowledgeIngestResponse:
    context = TenantService(db).resolve(payload.organization_id)
    documents, chunks, source = KnowledgeService(db, context).ingest_path(payload.path, payload.source)
    db.commit()
    return KnowledgeIngestResponse(source=source, documents=documents, chunks=chunks)


@router.post("/upload", response_model=KnowledgeIngestResponse)
async def upload_knowledge(
    organization_id: int | None = None,
    source: str | None = None,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> KnowledgeIngestResponse:
    try:
        content = await read_upload_text(file)
        context = TenantService(db).resolve(organization_id)
        service = KnowledgeService(db, context)
        documents = service.parse_upload(file.filename or "upload.txt", content)
        document_count, chunk_count, source_name = service.ingest_documents(
            documents,
            source or file.filename or "upload",
        )
        db.add(
            RAGIngestionJob(
                organization_id=context.organization_id,
                business_id=context.business_id,
                source=source_name,
                status="completed",
                documents=document_count,
                chunks=chunk_count,
            )
        )
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="Uploaded file must be UTF-8 text.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    db.commit()
    return KnowledgeIngestResponse(source=source_name, documents=document_count, chunks=chunk_count)


async def read_upload_text(file: UploadFile) -> str:
    content = bytearray()
    while chunk := await file.read(1024 * 1024):
        content.extend(chunk)
        if len(content) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Uploaded file exceeds {settings.max_upload_bytes} bytes.",
            )
    return bytes(content).decode("utf-8")
