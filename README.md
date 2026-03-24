# deci-doc

[![Built with Claude Code](https://img.shields.io/badge/Built%20with-Claude%20Code-blue?logo=anthropic&logoColor=white)](https://claude.ai/code)


**Create, track, and search Architecture Decision Records (ADRs) and RFCs in your repo.**

Every architecture decision your team makes should be documented. deci-doc makes it frictionless: one command to create, search by content, track status lifecycle, link related decisions, and visualize the decision graph.

## Why deci-doc?

- **Zero dependencies** -- just Click for the CLI, no database required. Everything is plain Markdown files in your repo.
- **Two document types** -- ADRs (Architecture Decision Records) and RFCs (Requests for Comments) with appropriate templates
- **Full lifecycle** -- proposed -> accepted -> deprecated -> superseded, with supersedence chains
- **Full-text search** -- search by content, status, date range, or tags with relevance scoring
- **Relationship tracking** -- link related decisions, mark supersedence, visualize the entire decision graph
- **Team-friendly** -- Markdown files live in your repo, show up in PRs, and work with any Git workflow

## Install

```bash
pip install deci-doc
```

## Quick Start

```bash
# Create your first ADR
deci-doc new "Use PostgreSQL for user authentication"

# Create an RFC
deci-doc new "Migrate to microservices architecture" --type rfc --author "Jane Doe" --tag architecture

# List all decisions
deci-doc list

# Search across all decisions
deci-doc search "PostgreSQL"

# Update status
deci-doc status 1 accepted

# Link related decisions
deci-doc link 1 2

# Mark one as superseded
deci-doc supersede 1 3

# Visualize the decision graph
deci-doc graph

# Show chronological timeline
deci-doc timeline
```

## What Gets Created

```
docs/decisions/
  0001-use-postgresql-for-user-authentication.md
  0002-migrate-to-microservices-architecture.md
  0003-switch-to-cockroachdb-for-multi-region.md
```

### ADR Template
```markdown
# 0001. Use PostgreSQL for user authentication

**Date:** 2026-03-24
**Status:** Accepted
**Authors:** Jane Doe
**Tags:** database, authentication

## Context

We need a reliable database for storing user credentials and session data...

## Decision

We will use PostgreSQL 16 with row-level security...

## Consequences

- Positive: ACID compliance, mature ecosystem
- Negative: Single-region limitation, need migration tooling
```

### RFC Template
Includes Problem Statement, Proposed Solution, Alternatives Considered, and Timeline sections.

## Commands

| Command | Description |
|---------|-------------|
| `deci-doc new "title"` | Create a new ADR or RFC |
| `deci-doc list` | List all decisions with filters |
| `deci-doc search "query"` | Full-text search with relevance scoring |
| `deci-doc status <id> <status>` | Update decision status |
| `deci-doc link <id1> <id2>` | Link two related decisions |
| `deci-doc supersede <old> <new>` | Mark a decision as superseded |
| `deci-doc graph` | Visualize decision relationships |
| `deci-doc timeline` | Chronological timeline view |
| `deci-doc show <id>` | Display full decision content |

## Search

```bash
# Search by content
deci-doc search "microservices"

# Filter by status
deci-doc list --status accepted

# Filter by type and tag
deci-doc list --type rfc --tag architecture
```

Search scores results by relevance, weighting title matches higher than body content, and shows which fields matched.

## Decision Graph

```bash
# ASCII
deci-doc graph

# Decision Graph
# ============================================================
#   [+] 0001 [ADR] Use PostgreSQL for auth (accepted)
#       |-> superseded by: 0003
#       <-> related: 0002
#   [?] 0002 [RFC] Migrate to microservices (proposed)
#       <-> related: 0001
#   [+] 0003 [ADR] Switch to CockroachDB (accepted)
#       ^-- supersedes: 0001

# Mermaid (for GitHub docs)
deci-doc graph --format mermaid
```

## Python API

```python
from deci_doc.manager import DocumentManager
from deci_doc.searcher import Searcher

manager = DocumentManager("docs/decisions")
doc = manager.create(title="Use Redis for caching", tags=["caching", "performance"])

searcher = Searcher(manager)
results = searcher.search("caching", status="accepted")
```

## License

MIT
