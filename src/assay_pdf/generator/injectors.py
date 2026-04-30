"""Low-level PDF mutation helpers shared across rule generators.

Keeps rules.py concise — each rule generator builds the base, calls one or two
helpers from here to inject the violation, then stamps deterministic + returns
its ManifestEntry.
"""

from __future__ import annotations

import pikepdf


def append_content_stream(pdf: pikepdf.Pdf, page: pikepdf.Page, content_bytes: bytes) -> None:
    """Append ``content_bytes`` to a page's content stream array."""
    new_stream = pdf.make_stream(content_bytes)
    existing = page.Contents
    if isinstance(existing, pikepdf.Array):
        existing.append(new_stream)
    else:
        page.Contents = pikepdf.Array([existing, new_stream])


def _slash(name: str) -> str:
    """Ensure a PDF Name string starts with '/'."""
    return name if name.startswith("/") else f"/{name}"


def add_font_resource(
    page: pikepdf.Page,
    *,
    name: str,
    base_font: str,
    subtype: str = "/Type1",
    encoding: str = "/WinAnsiEncoding",
) -> None:
    """Add a font resource to a page under the given resource-dict name."""
    if "/Resources" not in page:
        page.Resources = pikepdf.Dictionary({})
    if "/Font" not in page.Resources:
        page.Resources["/Font"] = pikepdf.Dictionary({})
    page.Resources["/Font"][f"/{name}"] = pikepdf.Dictionary(
        {
            "/Type": pikepdf.Name("/Font"),
            "/Subtype": pikepdf.Name(_slash(subtype)),
            "/BaseFont": pikepdf.Name(_slash(base_font)),
            "/Encoding": pikepdf.Name(_slash(encoding)),
        }
    )


def cmyk_fill_op(c: float, m: float, y: float, k: float) -> bytes:
    """CMYK fill color set operator string."""
    return f"{c:.2f} {m:.2f} {y:.2f} {k:.2f} k\n".encode()


def cmyk_stroke_op(c: float, m: float, y: float, k: float) -> bytes:
    """CMYK stroke color set operator string."""
    return f"{c:.2f} {m:.2f} {y:.2f} {k:.2f} K\n".encode()


def overprint_state(stroke: bool = False, fill: bool = True, opm: int = 1) -> bytes:
    """Inline ExtGState content stream snippet that turns on overprint.

    Sets /OP (stroke), /op (fill), and /OPM (overprint mode).
    Returns the operator bytes; caller must add /GSx to /Resources/ExtGState.
    """
    return (
        f"<</Type /ExtGState /OP {str(stroke).lower()} /op {str(fill).lower()} /OPM {opm}>> /GSop gs\n"
    ).encode()


def add_extgstate(
    page: pikepdf.Page,
    *,
    name: str,
    op_stroke: bool = False,
    op_fill: bool = False,
    opm: int = 0,
) -> None:
    """Add an ExtGState resource for overprint control."""
    if "/Resources" not in page:
        page.Resources = pikepdf.Dictionary({})
    if "/ExtGState" not in page.Resources:
        page.Resources["/ExtGState"] = pikepdf.Dictionary({})
    page.Resources["/ExtGState"][f"/{name}"] = pikepdf.Dictionary(
        {
            "/Type": pikepdf.Name("/ExtGState"),
            "/OP": op_stroke,
            "/op": op_fill,
            "/OPM": opm,
        }
    )
