from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional


class RefundSource(str, Enum):
    """Describes who initiated the refund."""

    USER = "USER"
    BACKOFFICE = "BACKOFFICE"


class RefundStatus(str, Enum):
    """Lifecycle states an individual refund request can be in."""

    PENDING_REVIEW = "PENDING_REVIEW"
    REJECTED = "REJECTED"
    REMOTE_PROCESSING = "REMOTE_PROCESSING"
    REFUND_FAILED = "REFUND_FAILED"
    REFUNDED = "REFUNDED"


@dataclass
class RefundRequest:
    """Domain model stored inside the repository."""

    id: str
    order_id: str
    user_id: str
    amount: Decimal
    reason: str
    source: RefundSource
    status: RefundStatus
    created_at: datetime
    updated_at: datetime
    operator_id: Optional[str] = None
    audit_notes: Optional[str] = None
    failure_reason: Optional[str] = None
    remote_attempt_count: int = 0
    manual_retry_count: int = 0

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc)
