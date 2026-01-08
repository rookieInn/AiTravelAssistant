"""
Finance helpers for:
- RMB uppercase amount conversion (人民币金额大写)
- Tax-inclusive/exclusive conversion and rounding-safe line splitting (税额拆分)
"""

from .rmb import rmb_upper
from .tax import TaxLine, TaxResult, compute_tax, split_tax_lines

__all__ = [
    "rmb_upper",
    "TaxLine",
    "TaxResult",
    "compute_tax",
    "split_tax_lines",
]

