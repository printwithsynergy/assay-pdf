"""AssayPDF CLI entrypoint.

Stub for Commit 1 — full subcommand wiring lands in Commit 2 (spec ingestion).
"""

from __future__ import annotations

import typer

from assay_pdf import __version__

app = typer.Typer(
    name="assay",
    help="Open-source GWG 2022 conformance assay for PDF preflight engines.",
    no_args_is_help=True,
    add_completion=False,
)


@app.command()
def version() -> None:
    """Print AssayPDF version."""
    typer.echo(f"AssayPDF {__version__}")


# Subcommands wired in Commit 2:
#   assay fetch      — download GWG vendor assets
#   assay ingest     — parse spec/gwg-2022-spec.xlsx → spec/requirement-ids.json
#   assay generate   — generate the corpus
#   assay benchmark  — run engine against corpus
#   assay report     — render scoreboard
#   assay validate   — verapdf validation pass


if __name__ == "__main__":
    app()
