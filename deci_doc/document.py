"""ADR document model with status lifecycle management."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any


class DocStatus(str, Enum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"

    @classmethod
    def from_str(cls, s: str) -> "DocStatus":
        try:
            return cls(s.lower().strip())
        except ValueError:
            raise ValueError(
                f"Invalid status: {s!r}. Must be one of: "
                + ", ".join(v.value for v in cls)
            )


class DocType(str, Enum):
    ADR = "adr"
    RFC = "rfc"


@dataclass
class Decision:
    """Represents an Architecture Decision Record or RFC."""
    id: int
    title: str
    status: DocStatus = DocStatus.PROPOSED
    doc_type: DocType = DocType.ADR
    date_created: str = ""
    date_updated: str = ""
    context: str = ""
    decision: str = ""
    consequences: str = ""
    # RFC-specific fields
    problem_statement: str = ""
    proposed_solution: str = ""
    alternatives: str = ""
    timeline: str = ""
    # Relationships
    links: list[int] = field(default_factory=list)
    superseded_by: int | None = None
    supersedes: int | None = None
    # Metadata
    authors: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.date_created:
            self.date_created = date.today().isoformat()
        if not self.date_updated:
            self.date_updated = self.date_created

    @property
    def filename(self) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", self.title.lower()).strip("-")
        slug = slug[:60]  # Limit length
        return f"{self.id:04d}-{slug}.md"

    @property
    def is_active(self) -> bool:
        return self.status in (DocStatus.PROPOSED, DocStatus.ACCEPTED)

    def update_status(self, new_status: DocStatus):
        """Update the status and set the updated date."""
        self.status = new_status
        self.date_updated = date.today().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status.value,
            "doc_type": self.doc_type.value,
            "date_created": self.date_created,
            "date_updated": self.date_updated,
            "context": self.context,
            "decision": self.decision,
            "consequences": self.consequences,
            "problem_statement": self.problem_statement,
            "proposed_solution": self.proposed_solution,
            "alternatives": self.alternatives,
            "timeline": self.timeline,
            "links": self.links,
            "superseded_by": self.superseded_by,
            "supersedes": self.supersedes,
            "authors": self.authors,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Decision":
        return cls(
            id=data["id"],
            title=data["title"],
            status=DocStatus.from_str(data.get("status", "proposed")),
            doc_type=DocType(data.get("doc_type", "adr")),
            date_created=data.get("date_created", ""),
            date_updated=data.get("date_updated", ""),
            context=data.get("context", ""),
            decision=data.get("decision", ""),
            consequences=data.get("consequences", ""),
            problem_statement=data.get("problem_statement", ""),
            proposed_solution=data.get("proposed_solution", ""),
            alternatives=data.get("alternatives", ""),
            timeline=data.get("timeline", ""),
            links=data.get("links", []),
            superseded_by=data.get("superseded_by"),
            supersedes=data.get("supersedes"),
            authors=data.get("authors", []),
            tags=data.get("tags", []),
        )
