"""Full-text search across all ADRs and RFCs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any

from .document import Decision, DocStatus
from .manager import DocumentManager


@dataclass
class SearchResult:
    """A single search result with relevance information."""
    document: Decision
    score: float
    matched_fields: list[str]
    snippet: str = ""


def _text_score(text: str, query: str) -> float:
    """Score text relevance to a query (simple TF-based scoring)."""
    if not text or not query:
        return 0.0

    text_lower = text.lower()
    query_lower = query.lower()
    words = query_lower.split()

    score = 0.0

    # Exact phrase match (highest weight)
    if query_lower in text_lower:
        score += 10.0

    # Individual word matches
    for word in words:
        count = text_lower.count(word)
        if count > 0:
            score += count * 2.0
            # Bonus for word appearing in first 200 chars
            if word in text_lower[:200]:
                score += 3.0

    return score


def _extract_snippet(text: str, query: str, context_chars: int = 120) -> str:
    """Extract a relevant snippet from text around the query match."""
    if not text or not query:
        return ""

    text_lower = text.lower()
    query_lower = query.lower()

    # Find first occurrence of query or first query word
    pos = text_lower.find(query_lower)
    if pos == -1:
        for word in query_lower.split():
            pos = text_lower.find(word)
            if pos != -1:
                break

    if pos == -1:
        return text[:context_chars * 2] + "..." if len(text) > context_chars * 2 else text

    start = max(0, pos - context_chars)
    end = min(len(text), pos + len(query) + context_chars)

    snippet = text[start:end].replace("\n", " ").strip()
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return snippet


class Searcher:
    """Full-text search engine for ADR/RFC documents."""

    # Field weights for scoring
    FIELD_WEIGHTS = {
        "title": 5.0,
        "decision": 3.0,
        "context": 2.0,
        "consequences": 2.0,
        "problem_statement": 3.0,
        "proposed_solution": 3.0,
        "alternatives": 1.5,
        "tags": 4.0,
    }

    def __init__(self, manager: DocumentManager):
        self.manager = manager

    def search(
        self,
        query: str,
        status: str | None = None,
        doc_type: str | None = None,
        tags: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 20,
    ) -> list[SearchResult]:
        """Search across all documents.

        Args:
            query: Search query string.
            status: Filter by status (proposed, accepted, deprecated, superseded).
            doc_type: Filter by type (adr, rfc).
            tags: Filter by tags (any match).
            date_from: Filter by creation date (inclusive, ISO format).
            date_to: Filter by creation date (inclusive, ISO format).
            limit: Maximum results to return.

        Returns:
            List of SearchResult sorted by relevance score.
        """
        documents = self.manager.list_all()
        results: list[SearchResult] = []

        for doc in documents:
            # Apply filters
            if status and doc.status.value != status.lower():
                continue
            if doc_type and doc.doc_type.value != doc_type.lower():
                continue
            if tags and not any(t in doc.tags for t in tags):
                continue
            if date_from and doc.date_created < date_from:
                continue
            if date_to and doc.date_created > date_to:
                continue

            # Score the document
            if not query:
                # No query, just filter results
                results.append(SearchResult(
                    document=doc, score=1.0,
                    matched_fields=[], snippet=doc.title,
                ))
                continue

            total_score = 0.0
            matched: list[str] = []
            best_snippet = ""
            best_snippet_score = 0.0

            for field_name, weight in self.FIELD_WEIGHTS.items():
                text = getattr(doc, field_name, "")
                if isinstance(text, list):
                    text = " ".join(text)
                if not text:
                    continue

                raw_score = _text_score(text, query)
                if raw_score > 0:
                    weighted = raw_score * weight
                    total_score += weighted
                    matched.append(field_name)

                    if raw_score > best_snippet_score and field_name not in ("tags", "title"):
                        best_snippet_score = raw_score
                        best_snippet = _extract_snippet(text, query)

            if total_score > 0:
                if not best_snippet:
                    best_snippet = doc.title
                results.append(SearchResult(
                    document=doc,
                    score=total_score,
                    matched_fields=matched,
                    snippet=best_snippet,
                ))

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def search_by_keyword(self, keyword: str) -> list[Decision]:
        """Simple keyword search returning matching documents."""
        results = self.search(keyword)
        return [r.document for r in results]

    def get_by_status(self, status: str) -> list[Decision]:
        """Get all documents with a given status."""
        results = self.search("", status=status)
        return [r.document for r in results]

    def get_by_tags(self, tags: list[str]) -> list[Decision]:
        """Get all documents matching any of the given tags."""
        results = self.search("", tags=tags)
        return [r.document for r in results]
