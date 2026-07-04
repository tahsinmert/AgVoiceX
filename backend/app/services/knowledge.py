import csv
import json
from pathlib import Path

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.knowledge_chunks import KnowledgeChunk
from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import KnowledgeCreate
from app.services.tenancy import TenantContext, TenantService


class KnowledgeService:
    def __init__(self, db: Session, tenant_context: TenantContext | None = None):
        self.db = db
        self.tenant_context = tenant_context or TenantService(db).get_or_create_default_context()

    def create(self, data: KnowledgeCreate) -> KnowledgeItem:
        item = KnowledgeItem(
            organization_id=self.tenant_context.organization_id,
            title=data.title,
            body=data.body,
            source=data.source,
            item_metadata=data.metadata,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def search(self, query: str, limit: int = 5) -> list[KnowledgeItem]:
        pattern = f"%{query}%"
        statement = (
            select(KnowledgeItem)
            .where(
                KnowledgeItem.organization_id == self.tenant_context.organization_id,
                or_(KnowledgeItem.title.ilike(pattern), KnowledgeItem.body.ilike(pattern)),
            )
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    def search_chunks(self, query: str, limit: int = 5) -> list[KnowledgeChunk]:
        pattern = f"%{query}%"
        statement = (
            select(KnowledgeChunk)
            .where(
                KnowledgeChunk.organization_id == self.tenant_context.organization_id,
                KnowledgeChunk.body.ilike(pattern),
            )
            .limit(limit)
        )
        return list(self.db.scalars(statement))

    def ingest_path(self, path: str, source: str | None = None) -> tuple[int, int, str]:
        target = self._resolve_allowed_path(path)
        if not target.exists():
            raise ValueError(f"File does not exist: {path}")
        if not target.is_file():
            raise ValueError("Knowledge ingestion path must be a file.")
        documents = self._load_documents(target)
        source_name = source or target.name
        document_count = 0
        chunk_count = 0
        for title, body in documents:
            item = self.create(KnowledgeCreate(title=title, body=body, source=source_name))
            document_count += 1
            for chunk_index, chunk in enumerate(self._chunk_text(body)):
                self.db.add(
                    KnowledgeChunk(
                        organization_id=self.tenant_context.organization_id,
                        knowledge_id=item.id,
                        chunk_index=chunk_index,
                        body=chunk,
                        source=source_name,
                        chunk_metadata={"path": str(target)},
                    )
                )
                chunk_count += 1
        self.db.flush()
        return document_count, chunk_count, source_name

    def ingest_documents(self, documents: list[tuple[str, str]], source: str) -> tuple[int, int, str]:
        document_count = 0
        chunk_count = 0
        for title, body in documents:
            item = self.create(KnowledgeCreate(title=title, body=body, source=source))
            document_count += 1
            for chunk_index, chunk in enumerate(self._chunk_text(body)):
                self.db.add(
                    KnowledgeChunk(
                        organization_id=self.tenant_context.organization_id,
                        knowledge_id=item.id,
                        chunk_index=chunk_index,
                        body=chunk,
                        source=source,
                        chunk_metadata={"uploaded": True},
                    )
                )
                chunk_count += 1
        self.db.flush()
        return document_count, chunk_count, source

    def parse_upload(self, filename: str, content: str) -> list[tuple[str, str]]:
        path = Path(filename).name
        safe_path = Path(path)
        if len(path) > 255:
            raise ValueError("Uploaded filename is too long.")
        suffix = safe_path.suffix.lower()
        if suffix in {".txt", ".md", ".markdown"}:
            return [(safe_path.stem, content)]
        if suffix == ".json":
            data = json.loads(content)
            if isinstance(data, list):
                return [
                    (
                        str(item.get("title", safe_path.stem)) if isinstance(item, dict) else safe_path.stem,
                        json.dumps(item, ensure_ascii=False),
                    )
                    for item in data
                ]
            return [(str(data.get("title", safe_path.stem)) if isinstance(data, dict) else safe_path.stem, json.dumps(data))]
        if suffix == ".csv":
            rows = list(csv.DictReader(content.splitlines()))
            return [(f"{safe_path.stem} row {index + 1}", json.dumps(row, ensure_ascii=False)) for index, row in enumerate(rows)]
        raise ValueError("Supported ingestion formats: .txt, .md, .markdown, .json, .csv")

    def _load_documents(self, path: Path) -> list[tuple[str, str]]:
        suffix = path.suffix.lower()
        if suffix in {".txt", ".md", ".markdown"}:
            return [(path.stem, path.read_text(encoding="utf-8"))]
        if suffix == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [(str(item.get("title", path.stem)), json.dumps(item, ensure_ascii=False)) for item in data]
            return [(str(data.get("title", path.stem)) if isinstance(data, dict) else path.stem, json.dumps(data))]
        if suffix == ".csv":
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            return [(f"{path.stem} row {index + 1}", json.dumps(row, ensure_ascii=False)) for index, row in enumerate(rows)]
        raise ValueError("Supported ingestion formats: .txt, .md, .markdown, .json, .csv")

    @staticmethod
    def _resolve_allowed_path(path: str) -> Path:
        target = Path(path).expanduser().resolve()
        allowed_roots = [Path(root).expanduser().resolve() for root in settings.ingest_roots]
        if not any(target == root or target.is_relative_to(root) for root in allowed_roots):
            allowed = ", ".join(str(root) for root in allowed_roots)
            raise ValueError(f"Ingestion path must be under one of: {allowed}")
        return target

    @staticmethod
    def _chunk_text(body: str, max_chars: int = 1000) -> list[str]:
        paragraphs = [paragraph.strip() for paragraph in body.split("\n\n") if paragraph.strip()]
        chunks: list[str] = []
        current = ""
        for paragraph in paragraphs or [body]:
            if len(current) + len(paragraph) + 2 <= max_chars:
                current = f"{current}\n\n{paragraph}".strip()
            else:
                if current:
                    chunks.append(current)
                current = paragraph[:max_chars]
        if current:
            chunks.append(current)
        return chunks
