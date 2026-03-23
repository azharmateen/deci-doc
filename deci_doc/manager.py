"""Document manager: create, update, link, and manage ADR/RFC files."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .document import Decision, DocStatus, DocType
from .templates import render_document, parse_frontmatter


DEFAULT_DIR = "docs/decisions"


class DocumentManager:
    """Manages ADR/RFC documents on disk."""

    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or DEFAULT_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_next_id(self) -> int:
        """Get the next available document ID."""
        existing = self.list_all()
        if not existing:
            return 1
        return max(doc.id for doc in existing) + 1

    def _find_file(self, doc_id: int) -> Path | None:
        """Find the file for a given document ID."""
        pattern = f"{doc_id:04d}-*.md"
        matches = list(self.base_dir.glob(pattern))
        return matches[0] if matches else None

    def create(
        self,
        title: str,
        doc_type: DocType = DocType.ADR,
        context: str = "",
        decision: str = "",
        consequences: str = "",
        problem_statement: str = "",
        proposed_solution: str = "",
        alternatives: str = "",
        timeline: str = "",
        authors: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> Decision:
        """Create a new ADR or RFC document.

        Args:
            title: Decision title.
            doc_type: Type of document (ADR or RFC).
            context: Context section content.
            decision: Decision section content.
            consequences: Consequences section content.
            problem_statement: RFC problem statement.
            proposed_solution: RFC proposed solution.
            alternatives: RFC alternatives considered.
            timeline: RFC implementation timeline.
            authors: List of author names.
            tags: List of tags.

        Returns:
            The created Decision object.
        """
        doc_id = self._get_next_id()
        doc = Decision(
            id=doc_id,
            title=title,
            doc_type=doc_type,
            context=context,
            decision=decision,
            consequences=consequences,
            problem_statement=problem_statement,
            proposed_solution=proposed_solution,
            alternatives=alternatives,
            timeline=timeline,
            authors=authors or [],
            tags=tags or [],
        )

        content = render_document(doc)
        filepath = self.base_dir / doc.filename
        filepath.write_text(content, encoding="utf-8")
        return doc

    def get(self, doc_id: int) -> Decision | None:
        """Get a document by ID."""
        filepath = self._find_file(doc_id)
        if filepath is None:
            return None
        return self._load_from_file(filepath)

    def _load_from_file(self, filepath: Path) -> Decision:
        """Load a Decision from a markdown file."""
        content = filepath.read_text(encoding="utf-8")
        metadata = parse_frontmatter(content)

        # Extract ID from filename if not in metadata
        fname = filepath.stem
        if "id" not in metadata:
            match = re.match(r"(\d+)", fname)
            if match:
                metadata["id"] = int(match.group(1))

        # Parse sections
        sections = self._parse_sections(content)

        doc_type = DocType(metadata.get("doc_type", "adr"))

        return Decision(
            id=metadata.get("id", 0),
            title=metadata.get("title", fname),
            status=DocStatus.from_str(metadata.get("status", "proposed")),
            doc_type=doc_type,
            date_created=metadata.get("date_created", ""),
            date_updated=metadata.get("date_updated", ""),
            context=sections.get("Context", sections.get("Additional Context", "")),
            decision=sections.get("Decision", ""),
            consequences=sections.get("Consequences", sections.get("Expected Consequences", "")),
            problem_statement=sections.get("Problem Statement", ""),
            proposed_solution=sections.get("Proposed Solution", ""),
            alternatives=sections.get("Alternatives Considered", ""),
            timeline=sections.get("Timeline", ""),
            authors=metadata.get("authors", []),
            tags=metadata.get("tags", []),
        )

    def _parse_sections(self, content: str) -> dict[str, str]:
        """Parse markdown sections (## Heading -> content)."""
        sections: dict[str, str] = {}
        current_section = ""
        current_lines: list[str] = []

        for line in content.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_lines).strip()
                current_section = line[3:].strip()
                current_lines = []
            elif current_section:
                current_lines.append(line)

        if current_section:
            sections[current_section] = "\n".join(current_lines).strip()

        return sections

    def update_status(self, doc_id: int, new_status: str) -> Decision | None:
        """Update the status of a document.

        Args:
            doc_id: Document ID.
            new_status: New status string.

        Returns:
            Updated Decision or None if not found.
        """
        doc = self.get(doc_id)
        if doc is None:
            return None

        doc.update_status(DocStatus.from_str(new_status))
        self._save(doc)
        return doc

    def link(self, id1: int, id2: int) -> tuple[Decision, Decision] | None:
        """Create a bidirectional link between two documents.

        Returns:
            Tuple of updated documents or None if either not found.
        """
        doc1 = self.get(id1)
        doc2 = self.get(id2)
        if doc1 is None or doc2 is None:
            return None

        if id2 not in doc1.links:
            doc1.links.append(id2)
        if id1 not in doc2.links:
            doc2.links.append(id1)

        self._save(doc1)
        self._save(doc2)
        return (doc1, doc2)

    def supersede(self, old_id: int, new_id: int) -> tuple[Decision, Decision] | None:
        """Mark one document as superseded by another.

        Args:
            old_id: ID of the document being superseded.
            new_id: ID of the superseding document.

        Returns:
            Tuple of (old_doc, new_doc) or None if either not found.
        """
        old_doc = self.get(old_id)
        new_doc = self.get(new_id)
        if old_doc is None or new_doc is None:
            return None

        old_doc.update_status(DocStatus.SUPERSEDED)
        old_doc.superseded_by = new_id
        new_doc.supersedes = old_id

        self._save(old_doc)
        self._save(new_doc)
        return (old_doc, new_doc)

    def list_all(self) -> list[Decision]:
        """List all documents, sorted by ID."""
        docs: list[Decision] = []
        for filepath in sorted(self.base_dir.glob("*.md")):
            try:
                doc = self._load_from_file(filepath)
                docs.append(doc)
            except Exception:
                continue
        return docs

    def _save(self, doc: Decision):
        """Save a document, removing old file if filename changed."""
        # Remove old file
        old_file = self._find_file(doc.id)
        if old_file:
            old_file.unlink()

        content = render_document(doc)
        filepath = self.base_dir / doc.filename
        filepath.write_text(content, encoding="utf-8")

    def delete(self, doc_id: int) -> bool:
        """Delete a document by ID."""
        filepath = self._find_file(doc_id)
        if filepath:
            filepath.unlink()
            return True
        return False
