"""Visualize ADR relationships and supersedence chains as Mermaid diagrams."""

from __future__ import annotations

from .document import Decision, DocStatus, DocType
from .manager import DocumentManager


class Visualizer:
    """Generate visual representations of decision relationships."""

    def __init__(self, manager: DocumentManager):
        self.manager = manager

    def to_mermaid(self) -> str:
        """Generate a Mermaid diagram showing all decisions and their relationships."""
        docs = self.manager.list_all()
        if not docs:
            return "graph TD\n    empty[No decisions found]"

        lines = ["graph TD"]

        # Define node styles by status
        status_styles = {
            DocStatus.PROPOSED: "proposed",
            DocStatus.ACCEPTED: "accepted",
            DocStatus.DEPRECATED: "deprecated",
            DocStatus.SUPERSEDED: "superseded",
        }

        # Define nodes
        for doc in docs:
            label = f"{doc.id:04d}: {doc.title}"
            style_class = status_styles.get(doc.status, "proposed")
            node_id = f"d{doc.id}"

            if doc.doc_type == DocType.RFC:
                # Use rounded rectangle for RFCs
                lines.append(f'    {node_id}("{label}"):::{style_class}')
            else:
                # Use rectangle for ADRs
                lines.append(f'    {node_id}["{label}"]:::{style_class}')

        # Define edges
        for doc in docs:
            node_id = f"d{doc.id}"

            # Supersedence relationships
            if doc.superseded_by is not None:
                lines.append(f"    {node_id} -.->|superseded by| d{doc.superseded_by}")

            if doc.supersedes is not None:
                lines.append(f"    {node_id} ==>|supersedes| d{doc.supersedes}")

            # General links
            for link_id in doc.links:
                # Only add link in one direction to avoid duplicates
                if link_id > doc.id:
                    lines.append(f"    {node_id} <-->|related| d{link_id}")

        # Style definitions
        lines.extend([
            "",
            "    classDef proposed fill:#FFFACD,stroke:#DAA520,color:#333",
            "    classDef accepted fill:#90EE90,stroke:#228B22,color:#333",
            "    classDef deprecated fill:#D3D3D3,stroke:#808080,color:#666",
            "    classDef superseded fill:#FFB6C1,stroke:#DC143C,color:#333",
        ])

        return "\n".join(lines)

    def to_ascii(self) -> str:
        """Generate an ASCII representation of the decision graph."""
        docs = self.manager.list_all()
        if not docs:
            return "No decisions found."

        lines = [
            "Decision Graph",
            "=" * 60,
            "",
        ]

        status_icons = {
            DocStatus.PROPOSED: "?",
            DocStatus.ACCEPTED: "+",
            DocStatus.DEPRECATED: "-",
            DocStatus.SUPERSEDED: "x",
        }

        for doc in docs:
            icon = status_icons.get(doc.status, " ")
            type_tag = f"[{doc.doc_type.value.upper()}]"
            status_tag = f"({doc.status.value})"
            lines.append(f"  [{icon}] {doc.id:04d} {type_tag} {doc.title} {status_tag}")

            # Show relationships
            if doc.supersedes is not None:
                lines.append(f"      ^-- supersedes: {doc.supersedes:04d}")
            if doc.superseded_by is not None:
                lines.append(f"      |-> superseded by: {doc.superseded_by:04d}")
            if doc.links:
                related = ", ".join(f"{lid:04d}" for lid in doc.links)
                lines.append(f"      <-> related: {related}")
            if doc.tags:
                lines.append(f"      tags: {', '.join(doc.tags)}")

        lines.extend([
            "",
            "-" * 60,
            "Legend: [+] accepted  [?] proposed  [-] deprecated  [x] superseded",
        ])

        return "\n".join(lines)

    def get_supersedence_chains(self) -> list[list[int]]:
        """Find all supersedence chains (oldest -> newest)."""
        docs = {doc.id: doc for doc in self.manager.list_all()}
        visited: set[int] = set()
        chains: list[list[int]] = []

        for doc_id, doc in docs.items():
            if doc_id in visited:
                continue
            if doc.supersedes is not None or doc.superseded_by is not None:
                # Walk back to the root
                root = doc_id
                while docs.get(root) and docs[root].supersedes is not None:
                    root = docs[root].supersedes
                    if root in visited:
                        break

                # Walk forward to build chain
                chain: list[int] = []
                current = root
                while current is not None and current not in visited:
                    chain.append(current)
                    visited.add(current)
                    current_doc = docs.get(current)
                    current = current_doc.superseded_by if current_doc else None

                if len(chain) > 1:
                    chains.append(chain)

        return chains

    def get_timeline(self) -> str:
        """Generate a chronological timeline of decisions."""
        docs = sorted(self.manager.list_all(), key=lambda d: d.date_created)
        if not docs:
            return "No decisions found."

        lines = ["Decision Timeline", "=" * 60, ""]

        current_month = ""
        for doc in docs:
            month = doc.date_created[:7] if doc.date_created else "Unknown"
            if month != current_month:
                current_month = month
                lines.append(f"  {month}")
                lines.append(f"  {'-' * 40}")

            status_tag = f"[{doc.status.value}]"
            type_tag = doc.doc_type.value.upper()
            lines.append(f"    {doc.date_created} | {type_tag}-{doc.id:04d} {doc.title} {status_tag}")

        return "\n".join(lines)
