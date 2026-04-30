"""Rich-formatted logger for AssayPDF."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from rich.console import Console
from rich.logging import RichHandler

if TYPE_CHECKING:
    from collections.abc import Mapping

console = Console(stderr=True)


def configure_logging(level: str = "INFO", *, extra: Mapping[str, object] | None = None) -> None:
    """Initialize root logger with Rich formatting. Idempotent."""
    if logging.getLogger().handlers:
        return
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True, show_path=False)],
    )
    if extra:
        for k, v in extra.items():
            logging.info("%s = %s", k, v)


def get_logger(name: str) -> logging.Logger:
    """Get a module-scoped logger."""
    return logging.getLogger(name)
