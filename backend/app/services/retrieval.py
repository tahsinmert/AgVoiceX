from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.services.knowledge import KnowledgeService
from app.services.tenancy import TenantContext


@dataclass(frozen=True)
class RetrievalResult:
    source: str
    title: str
    body: str
    score: float


class HybridRetrievalService:
    def __init__(self, db: Session, context: TenantContext):
        self.db = db
        self.context = context
        self.knowledge = KnowledgeService(db, context)

    def search(self, query: str, limit: int = 5) -> list[RetrievalResult]:
        if not query.strip():
            return []
        results: list[RetrievalResult] = []
        for item in self.knowledge.search(query, limit=limit):
            results.append(
                RetrievalResult(
                    source=item.source or "knowledge",
                    title=item.title,
                    body=item.body,
                    score=self._lexical_score(query, f"{item.title} {item.body}"),
                )
            )
        remaining = max(limit - len(results), 0)
        if remaining:
            for chunk in self.knowledge.search_chunks(query, limit=remaining):
                results.append(
                    RetrievalResult(
                        source=chunk.source or "knowledge_chunk",
                        title=f"Chunk {chunk.chunk_index}",
                        body=chunk.body,
                        score=self._lexical_score(query, chunk.body),
                    )
                )
        return sorted(results, key=lambda result: result.score, reverse=True)[:limit]

    @staticmethod
    def _lexical_score(query: str, body: str) -> float:
        terms = {term.lower() for term in query.split() if term.strip()}
        if not terms:
            return 0
        haystack = body.lower()
        return sum(1 for term in terms if term in haystack) / len(terms)
