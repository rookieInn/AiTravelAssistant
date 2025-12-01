from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .models import RefundSource, RefundStatus


class RefundApplication(BaseModel):
    order_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
    amount: Decimal = Field(..., gt=0)
    reason: str = Field(..., min_length=1, max_length=500)


class BackendRefundRequest(RefundApplication):
    operator_id: str = Field(..., min_length=1)
    audit_notes: Optional[str] = Field(default=None, max_length=500)


class ReviewRequest(BaseModel):
    approve: bool
    operator_id: str = Field(..., min_length=1)
    audit_notes: Optional[str] = Field(default=None, max_length=500)


class RetryRequest(BaseModel):
    operator_id: str = Field(..., min_length=1)
    audit_notes: Optional[str] = Field(default=None, max_length=500)


class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    order_id: str
    user_id: str
    amount: Decimal
    reason: str
    source: RefundSource
    status: RefundStatus
    created_at: datetime
    updated_at: datetime
    operator_id: Optional[str]
    audit_notes: Optional[str]
    failure_reason: Optional[str]
    remote_attempt_count: int
    manual_retry_count: int


class RefundListResponse(BaseModel):
    items: List[RefundResponse]
