"""CLI for deci-doc: Architecture Decision Records and RFCs."""

from __future__ import annotations

import sys

import click

from .document import DocStatus, DocType
from .manager import DocumentManager
from .searcher import Searcher
from .visualizer import Visualizer


@click.group()
@click.version_option(package_name="deci-doc")
@click.option("--dir", "-d", "base_dir", default=None, help="Decision documents directory (default: docs/decisions)")
@click.pass_context
def cli(ctx, base_dir: str | None):
    """deci-doc: Create, track, and search Architecture Decision Records (ADRs) and RFCs."""
    ctx.ensure_object(dict)
    ctx.obj["manager"] = DocumentManager(base_dir)


@cli.command()
@click.argument("title")
@click.option("--type", "-t", "doc_type", default="adr", type=click.Choice(["adr", "rfc"]), help="Document type")
@click.option("--context", "-c", default="", help="Context/background for the decision")
@click.option("--decision", default="", help="The decision that was made")
@click.option("--consequences", default="", help="Consequences of the decision")
@click.option("--author", "-a", multiple=True, help="Author name(s)")
@click.option("--tag", multiple=True, help="Tags for categorization")
@click.pass_context
def new(ctx, title: str, doc_type: str, context: str, decision: str, consequences: str, author: tuple, tag: tuple):
    """Create a new ADR or RFC.

    Examples:
        deci-doc new "Use PostgreSQL for auth"
        deci-doc new "Migrate to microservices" --type rfc --author "Jane Doe" --tag architecture
    """
    manager: DocumentManager = ctx.obj["manager"]

    doc = manager.create(
        title=title,
        doc_type=DocType(doc_type),
        context=context,
        decision=decision,
        consequences=consequences,
        authors=list(author),
        tags=list(tag),
    )

    prefix = "ADR" if doc.doc_type == DocType.ADR else "RFC"
    click.secho(f"Created {prefix}-{doc.id:04d}: {doc.title}", fg="green")
    click.secho(f"  File: {manager.base_dir / doc.filename}", fg="cyan")
    click.secho(f"  Status: {doc.status.value}", fg="yellow")
    click.echo(f"\nEdit the file to fill in the details.")


@cli.command("list")
@click.option("--status", "-s", type=click.Choice(["proposed", "accepted", "deprecated", "superseded"]), help="Filter by status")
@click.option("--type", "-t", "doc_type", type=click.Choice(["adr", "rfc"]), help="Filter by type")
@click.option("--tag", multiple=True, help="Filter by tag")
@click.pass_context
def list_cmd(ctx, status: str | None, doc_type: str | None, tag: tuple):
    """List all decisions with optional filters.

    Examples:
        deci-doc list
        deci-doc list --status accepted
        deci-doc list --type rfc --tag architecture
    """
    manager: DocumentManager = ctx.obj["manager"]
    searcher = Searcher(manager)

    results = searcher.search(
        "",
        status=status,
        doc_type=doc_type,
        tags=list(tag) if tag else None,
    )

    if not results:
        click.secho("No decisions found.", fg="yellow")
        return

    status_colors = {
        "proposed": "yellow",
        "accepted": "green",
        "deprecated": "white",
        "superseded": "red",
    }

    for r in results:
        doc = r.document
        prefix = "ADR" if doc.doc_type == DocType.ADR else "RFC"
        color = status_colors.get(doc.status.value, "white")
        status_str = f"[{doc.status.value}]"
        tags_str = f" ({', '.join(doc.tags)})" if doc.tags else ""

        click.echo(
            click.style(f"  {prefix}-{doc.id:04d}", fg="cyan", bold=True)
            + " "
            + click.style(status_str, fg=color)
            + f" {doc.title}{tags_str}"
            + click.style(f"  {doc.date_created}", fg="white", dim=True)
        )

    click.echo(f"\n{len(results)} decision(s) found.")


@cli.command()
@click.argument("query")
@click.option("--status", "-s", help="Filter by status")
@click.option("--limit", "-n", default=20, help="Max results")
@click.pass_context
def search(ctx, query: str, status: str | None, limit: int):
    """Search across all decisions by content, title, or tags.

    Examples:
        deci-doc search "PostgreSQL"
        deci-doc search "authentication" --status accepted
    """
    manager: DocumentManager = ctx.obj["manager"]
    searcher = Searcher(manager)

    results = searcher.search(query, status=status, limit=limit)

    if not results:
        click.secho(f"No results for '{query}'.", fg="yellow")
        return

    for r in results:
        doc = r.document
        prefix = "ADR" if doc.doc_type == DocType.ADR else "RFC"
        fields = ", ".join(r.matched_fields)

        click.echo(
            click.style(f"  {prefix}-{doc.id:04d}", fg="cyan", bold=True)
            + f" [{doc.status.value}] {doc.title}"
            + click.style(f"  (score: {r.score:.1f}, matched: {fields})", fg="white", dim=True)
        )
        if r.snippet and r.snippet != doc.title:
            click.echo(click.style(f"    {r.snippet}", fg="white", dim=True))

    click.echo(f"\n{len(results)} result(s) found.")


@cli.command()
@click.argument("doc_id", type=int)
@click.argument("new_status", type=click.Choice(["proposed", "accepted", "deprecated", "superseded"]))
@click.pass_context
def status(ctx, doc_id: int, new_status: str):
    """Update the status of a decision.

    Examples:
        deci-doc status 1 accepted
        deci-doc status 3 deprecated
    """
    manager: DocumentManager = ctx.obj["manager"]
    doc = manager.update_status(doc_id, new_status)

    if doc is None:
        click.secho(f"Decision {doc_id:04d} not found.", fg="red")
        sys.exit(1)

    click.secho(f"Updated {doc.id:04d}: status -> {new_status}", fg="green")


@cli.command()
@click.argument("id1", type=int)
@click.argument("id2", type=int)
@click.pass_context
def link(ctx, id1: int, id2: int):
    """Create a bidirectional link between two decisions.

    Example:
        deci-doc link 1 3
    """
    manager: DocumentManager = ctx.obj["manager"]
    result = manager.link(id1, id2)

    if result is None:
        click.secho(f"One or both decisions not found ({id1:04d}, {id2:04d}).", fg="red")
        sys.exit(1)

    click.secho(f"Linked {id1:04d} <-> {id2:04d}", fg="green")


@cli.command()
@click.argument("old_id", type=int)
@click.argument("new_id", type=int)
@click.pass_context
def supersede(ctx, old_id: int, new_id: int):
    """Mark a decision as superseded by another.

    Example:
        deci-doc supersede 1 5
    """
    manager: DocumentManager = ctx.obj["manager"]
    result = manager.supersede(old_id, new_id)

    if result is None:
        click.secho(f"One or both decisions not found ({old_id:04d}, {new_id:04d}).", fg="red")
        sys.exit(1)

    click.secho(f"Marked {old_id:04d} as superseded by {new_id:04d}", fg="green")


@cli.command()
@click.option("--format", "-f", "fmt", default="ascii", type=click.Choice(["ascii", "mermaid"]), help="Output format")
@click.pass_context
def graph(ctx, fmt: str):
    """Visualize the decision relationship graph.

    Examples:
        deci-doc graph
        deci-doc graph --format mermaid
    """
    manager: DocumentManager = ctx.obj["manager"]
    viz = Visualizer(manager)

    if fmt == "mermaid":
        click.echo(viz.to_mermaid())
    else:
        click.echo(viz.to_ascii())

    # Show supersedence chains
    chains = viz.get_supersedence_chains()
    if chains:
        click.echo("\nSupersedence chains:")
        for chain in chains:
            chain_str = " -> ".join(f"{cid:04d}" for cid in chain)
            click.echo(f"  {chain_str}")


@cli.command()
@click.pass_context
def timeline(ctx):
    """Show a chronological timeline of all decisions.

    Example:
        deci-doc timeline
    """
    manager: DocumentManager = ctx.obj["manager"]
    viz = Visualizer(manager)
    click.echo(viz.get_timeline())


@cli.command()
@click.argument("doc_id", type=int)
@click.pass_context
def show(ctx, doc_id: int):
    """Show the full content of a decision.

    Example:
        deci-doc show 1
    """
    manager: DocumentManager = ctx.obj["manager"]
    doc = manager.get(doc_id)

    if doc is None:
        click.secho(f"Decision {doc_id:04d} not found.", fg="red")
        sys.exit(1)

    filepath = manager._find_file(doc_id)
    if filepath:
        click.echo(filepath.read_text(encoding="utf-8"))


if __name__ == "__main__":
    cli()
