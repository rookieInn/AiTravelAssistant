from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from .models import RefundRequest


@dataclass
class PaymentResult:
    success: bool
    code: str
    message: str


class PaymentGateway:
    """Very small fake payment gateway integration used for demos/tests."""

    def __init__(self, auto_refund_limit: Decimal = Decimal("1000")) -> None:
        self.auto_refund_limit = Decimal(auto_refund_limit)

    def process_refund(self, refund: RefundRequest) -> PaymentResult:
        if refund.amount > self.auto_refund_limit:
            return PaymentResult(
                success=False,
                code="LIMIT_EXCEEDED",
                message=(
                    "Requested amount exceeds the configured auto refund limit "
                    f"{self.auto_refund_limit}."
                ),
            )
        return PaymentResult(success=True, code="SUCCESS", message="Refund completed")
