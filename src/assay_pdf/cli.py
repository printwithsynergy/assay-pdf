"""AssayPDF CLI — `assay <subcommand>` entrypoint."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich import print as rprint

from assay_pdf import __version__
from assay_pdf.logging import configure_logging

app = typer.Typer(
    name="assay",
    help="Open-source GWG 2022 conformance assay for PDF preflight engines.",
    no_args_is_help=True,
    add_completion=False,
)


@app.callback()
def _root(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable debug logging.")] = False,
) -> None:
    """Configure logging once for the entire invocation."""
    configure_logging("DEBUG" if verbose else "INFO")


@app.command()
def version() -> None:
    """Print AssayPDF version."""
    rprint(f"[bold]AssayPDF[/bold] {__version__}")


@app.command()
def ingest(
    xlsx: Annotated[Path | None, typer.Option("--xlsx", help="Path to GWG 2022 XLSX (default: spec/gwg-2022-spec.xlsx).")] = None,
    output: Annotated[Path | None, typer.Option("--output", help="Where to write requirement-ids.json (default: spec/requirement-ids.json).")] = None,
) -> None:
    """Parse the GWG 2022 spec workbook into a machine-readable manifest."""
    from assay_pdf.spec.ingest import ingest as do_ingest

    out = do_ingest(xlsx, output)
    rprint(f"[green]✓[/green] {out}")


@app.command()
def fetch(
    force: Annotated[bool, typer.Option("--force", help="Re-download even if files exist with valid checksums.")] = False,
) -> None:
    """Download GWG vendor assets (~183 MB) into vendor/ with SHA-256 verification."""
    from assay_pdf.fetcher.download import fetch_all

    fetch_all(force=force)


@app.command()
def generate(
    only_rule: Annotated[str | None, typer.Option("--only-rule", help="Generate only files for one rule ID (e.g. R0014).")] = None,
    only_variant: Annotated[str | None, typer.Option("--only-variant", help="Generate only files for one variant kebab.")] = None,
    seed: Annotated[int, typer.Option("--seed", help="Deterministic generation seed.")] = 0,
) -> None:
    """Generate the PDF/X-4 corpus into corpus/."""
    from assay_pdf.generator.orchestrator import generate_corpus

    manifest = generate_corpus(only_rule=only_rule, only_variant=only_variant, seed=seed)
    rprint(f"[green]✓[/green] Generated {len(manifest.files)} PDFs")


@app.command()
def benchmark(
    engine: Annotated[str, typer.Option("--engine", help="Engine name: pdftoolbox, pitstop, lintpdf.")],
    profile: Annotated[str | None, typer.Option("--profile", help="GWG 2022 variant kebab name (omit to run all variants).")] = None,
) -> None:
    """Run an engine against the corpus and write results + score to results/."""
    from assay_pdf.harness.driver import benchmark as do_benchmark
    from assay_pdf.harness.runners import RunnerNotInstalledError

    try:
        score = do_benchmark(engine=engine, profile=profile)
    except RunnerNotInstalledError as e:
        rprint(f"[yellow]Engine not available[/yellow] — {e}")
        raise typer.Exit(code=2) from e

    total_tp = sum(s.true_positives for s in score.per_rule_per_variant)
    total_fp = sum(s.false_positives for s in score.per_rule_per_variant)
    total_fn = sum(s.false_negatives for s in score.per_rule_per_variant)
    total_tn = sum(s.true_negatives for s in score.per_rule_per_variant)
    rprint(
        f"[green]✓[/green] {engine} score: TP={total_tp} FP={total_fp} FN={total_fn} TN={total_tn} "
        f"({score.aggregate_runtime_ms}ms aggregate runtime)"
    )


@app.command()
def report(
    fmt: Annotated[str, typer.Option("--format", help="md or html.")] = "md",
) -> None:
    """Render the scoreboard from results/ (Commit 5 — not yet implemented)."""
    _ = fmt
    rprint("[yellow]Not yet implemented[/yellow] — lands in Commit 5.")
    raise typer.Exit(code=2)


@app.command()
def validate(
    schema_only: Annotated[bool, typer.Option("--schema-only", help="Skip verapdf; just validate manifests against schemas.")] = False,
) -> None:
    """Validate every corpus PDF against verapdf PDF/X-4."""
    from assay_pdf.generator.validation import validate_corpus

    failures = validate_corpus(schema_only=schema_only)
    if failures:
        rprint(f"[red]✗ {len(failures)} validation failure(s)[/red]")
        for path, msg in failures:
            rprint(f"  {path}: {msg}")
        raise typer.Exit(code=1)
    rprint("[green]✓[/green] All corpus PDFs valid")


if __name__ == "__main__":
    app()
