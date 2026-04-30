"""Deterministic PDF/X-4 corpus generator.

Public surface:
- ``generate_corpus`` — build the entire corpus into ``corpus/``
- ``RULE_GENERATORS`` — registry of {rule_id: generator_callable}
- ``VARIANTS`` — the 23 GWG 2022 variant configurations
"""

from assay_pdf.generator.registry import RULE_GENERATORS
from assay_pdf.generator.variants import VARIANTS

__all__ = ["RULE_GENERATORS", "VARIANTS"]
