from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from .exceptions import InvalidRefundStateError, RetryLimitExceededError
from .models import RefundRequest, RefundSource, RefundStatus
from .payment_gateway import PaymentGateway
from .storage import InMemoryRefundRepository


class RefundService:
    """Core domain service orchestrating refunds and payment calls."""

    def __init__(
        self,
        repository: Optional[InMemoryRefundRepository] = None,
        gateway: Optional[PaymentGateway] = None,
        max_manual_retries: int = 3,
    ) -> None:
        self.repository = repository or InMemoryRefundRepository()
        self.gateway = gateway or PaymentGateway()
        self.max_manual_retries = max_manual_retries

    def create_user_refund(
        self,
        order_id: str,
        user_id: str,
        amount: Decimal,
        reason: str,
    ) -> RefundRequest:
        now = datetime.now(timezone.utc)
        refund = RefundRequest(
            id=str(uuid4()),
            order_id=order_id,
            user_id=user_id,
            amount=self._normalize_amount(amount),
            reason=reason,
            source=RefundSource.USER,
            status=RefundStatus.PENDING_REVIEW,
            created_at=now,
            updated_at=now,
        )
        return self.repository.save(refund)

    def create_backend_refund(
        self,
        order_id: str,
        user_id: str,
        amount: Decimal,
        reason: str,
        operator_id: str,
        audit_notes: Optional[str] = None,
    ) -> RefundRequest:
        refund = self.create_user_refund(order_id, user_id, amount, reason)
        refund.source = RefundSource.BACKOFFICE
        return self._attempt_remote(refund, operator_id, audit_notes)

    def review_refund(
        self,
        refund_id: str,
        approve: bool,
        operator_id: str,
        audit_notes: Optional[str] = None,
    ) -> RefundRequest:
        refund = self.repository.get(refund_id)
        if refund.status != RefundStatus.PENDING_REVIEW:
            raise InvalidRefundStateError(
                f"Refund {refund_id} is not awaiting review (current: {refund.status})."
            )
        if not approve:
            refund.status = RefundStatus.REJECTED
            refund.operator_id = operator_id
            refund.audit_notes = audit_notes
            refund.touch()
            return self.repository.save(refund)
        return self._attempt_remote(refund, operator_id, audit_notes)

    def retry_refund(
        self,
        refund_id: str,
        operator_id: str,
        audit_notes: Optional[str] = None,
    ) -> RefundRequest:
        refund = self.repository.get(refund_id)
        if refund.status != RefundStatus.REFUND_FAILED:
            raise InvalidRefundStateError(
                f"Refund {refund_id} cannot be retried from status {refund.status}."
            )
        if refund.manual_retry_count >= self.max_manual_retries:
            raise RetryLimitExceededError(
                f"Refund {refund_id} exceeded max retry limit ({self.max_manual_retries})."
            )
        refund.manual_retry_count += 1
        refund.touch()
        return self._attempt_remote(refund, operator_id, audit_notes)

    def get_refund(self, refund_id: str) -> RefundRequest:
        return self.repository.get(refund_id)

    def list_refunds(self, status: Optional[RefundStatus] = None):
        return self.repository.list(status=status)

    def _attempt_remote(
        self,
        refund: RefundRequest,
        operator_id: str,
        audit_notes: Optional[str] = None,
    ) -> RefundRequest:
        refund.operator_id = operator_id
        refund.audit_notes = audit_notes
        refund.status = RefundStatus.REMOTE_PROCESSING
        refund.remote_attempt_count += 1
        refund.touch()
        self.repository.save(refund)

        result = self.gateway.process_refund(refund)

        refund.touch()
        if result.success:
            refund.status = RefundStatus.REFUNDED
            refund.failure_reason = None
        else:
            refund.status = RefundStatus.REFUND_FAILED
            refund.failure_reason = result.message
        return self.repository.save(refund)

    @staticmethod
    def _normalize_amount(amount: Decimal) -> Decimal:
        decimal_amount = Decimal(str(amount))
        if decimal_amount <= 0:
            raise ValueError("Refund amount must be greater than zero")
        return decimal_amount.quantize(Decimal("0.01"))
