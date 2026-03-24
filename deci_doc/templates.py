"""Markdown templates for ADR and RFC documents."""

from __future__ import annotations

from .document import Decision, DocType, DocStatus


def render_adr(doc: Decision) -> str:
    """Render an ADR as Markdown."""
    lines = [
        f"# {doc.id:04d}. {doc.title}",
        "",
        f"**Date:** {doc.date_created}",
        f"**Status:** {doc.status.value.capitalize()}",
    ]

    if doc.date_updated != doc.date_created:
        lines.append(f"**Updated:** {doc.date_updated}")

    if doc.authors:
        lines.append(f"**Authors:** {', '.join(doc.authors)}")

    if doc.tags:
        lines.append(f"**Tags:** {', '.join(doc.tags)}")

    if doc.supersedes is not None:
        lines.append(f"**Supersedes:** ADR-{doc.supersedes:04d}")

    if doc.superseded_by is not None:
        lines.append(f"**Superseded by:** ADR-{doc.superseded_by:04d}")

    if doc.links:
        related = ", ".join(f"ADR-{link:04d}" for link in doc.links)
        lines.append(f"**Related:** {related}")

    lines.extend([
        "",
        "## Context",
        "",
        doc.context or "_Describe the context and problem that motivates this decision._",
        "",
        "## Decision",
        "",
        doc.decision or "_Describe the decision that was made._",
        "",
        "## Consequences",
        "",
        doc.consequences or "_Describe the consequences of this decision, both positive and negative._",
        "",
    ])

    return "\n".join(lines)


def render_rfc(doc: Decision) -> str:
    """Render an RFC as Markdown."""
    lines = [
        f"# RFC-{doc.id:04d}: {doc.title}",
        "",
        f"**Date:** {doc.date_created}",
        f"**Status:** {doc.status.value.capitalize()}",
    ]

    if doc.date_updated != doc.date_created:
        lines.append(f"**Updated:** {doc.date_updated}")

    if doc.authors:
        lines.append(f"**Authors:** {', '.join(doc.authors)}")

    if doc.tags:
        lines.append(f"**Tags:** {', '.join(doc.tags)}")

    if doc.links:
        related = ", ".join(f"RFC-{link:04d}" for link in doc.links)
        lines.append(f"**Related:** {related}")

    lines.extend([
        "",
        "## Problem Statement",
        "",
        doc.problem_statement or "_Describe the problem this RFC aims to solve._",
        "",
        "## Proposed Solution",
        "",
        doc.proposed_solution or "_Describe the proposed solution in detail._",
        "",
        "## Alternatives Considered",
        "",
        doc.alternatives or "_List alternative approaches that were considered and why they were rejected._",
        "",
        "## Timeline",
        "",
        doc.timeline or "_Outline the expected timeline for implementation._",
        "",
    ])

    # Include ADR-style fields if present
    if doc.context:
        lines.extend(["## Additional Context", "", doc.context, ""])
    if doc.consequences:
        lines.extend(["## Expected Consequences", "", doc.consequences, ""])

    return "\n".join(lines)


def render_document(doc: Decision) -> str:
    """Render a document based on its type."""
    if doc.doc_type == DocType.RFC:
        return render_rfc(doc)
    return render_adr(doc)


def parse_frontmatter(content: str) -> dict:
    """Parse metadata from the beginning of a markdown document."""
    metadata: dict = {}
    lines = content.split("\n")

    for line in lines:
        line = line.strip()
        if line.startswith("# "):
            # Parse title: "# 0001. Title" or "# RFC-0001: Title"
            title_match = line[2:].strip()
            if ". " in title_match[:10]:
                parts = title_match.split(". ", 1)
                try:
                    metadata["id"] = int(parts[0])
                except ValueError:
                    pass
                metadata["title"] = parts[1] if len(parts) > 1 else ""
            elif ": " in title_match[:15]:
                parts = title_match.split(": ", 1)
                prefix = parts[0]
                if prefix.startswith("RFC-"):
                    try:
                        metadata["id"] = int(prefix[4:])
                    except ValueError:
                        pass
                    metadata["doc_type"] = "rfc"
                metadata["title"] = parts[1] if len(parts) > 1 else ""

        elif line.startswith("**Status:**"):
            status_str = line.replace("**Status:**", "").strip()
            metadata["status"] = status_str.lower()

        elif line.startswith("**Date:**"):
            metadata["date_created"] = line.replace("**Date:**", "").strip()

        elif line.startswith("**Updated:**"):
            metadata["date_updated"] = line.replace("**Updated:**", "").strip()

        elif line.startswith("**Authors:**"):
            authors = line.replace("**Authors:**", "").strip()
            metadata["authors"] = [a.strip() for a in authors.split(",")]

        elif line.startswith("**Tags:**"):
            tags = line.replace("**Tags:**", "").strip()
            metadata["tags"] = [t.strip() for t in tags.split(",")]

        elif line.startswith("**Related:**"):
            related = line.replace("**Related:**", "").strip()
            links = []
            for part in related.split(","):
                part = part.strip()
                # Parse "ADR-0002" or "RFC-0002" format
                for prefix in ("ADR-", "RFC-"):
                    if part.startswith(prefix):
                        try:
                            links.append(int(part[len(prefix):]))
                        except ValueError:
                            pass
            metadata["links"] = links

        elif line.startswith("**Supersedes:**"):
            val = line.replace("**Supersedes:**", "").strip()
            for prefix in ("ADR-", "RFC-"):
                if val.startswith(prefix):
                    try:
                        metadata["supersedes"] = int(val[len(prefix):])
                    except ValueError:
                        pass

        elif line.startswith("**Superseded by:**"):
            val = line.replace("**Superseded by:**", "").strip()
            for prefix in ("ADR-", "RFC-"):
                if val.startswith(prefix):
                    try:
                        metadata["superseded_by"] = int(val[len(prefix):])
                    except ValueError:
                        pass

    return metadata
