from __future__ import annotations

import copy
from threading import RLock
from typing import Dict, List, Optional

from .exceptions import RefundNotFoundError
from .models import RefundRequest, RefundStatus


class InMemoryRefundRepository:
    """Thread-safe in-memory persistence used by the sample service."""

    def __init__(self) -> None:
        self._items: Dict[str, RefundRequest] = {}
        self._lock = RLock()

    def save(self, refund: RefundRequest) -> RefundRequest:
        with self._lock:
            self._items[refund.id] = copy.deepcopy(refund)
            return copy.deepcopy(refund)

    def get(self, refund_id: str) -> RefundRequest:
        with self._lock:
            if refund_id not in self._items:
                raise RefundNotFoundError(f"Refund {refund_id} was not found")
            return copy.deepcopy(self._items[refund_id])

    def list(self, status: Optional[RefundStatus] = None) -> List[RefundRequest]:
        with self._lock:
            values = list(self._items.values())
        if status:
            values = [item for item in values if item.status == status]
        return [copy.deepcopy(item) for item in values]
