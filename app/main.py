from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status

from .exceptions import (
    InvalidRefundStateError,
    RefundNotFoundError,
    RetryLimitExceededError,
)
from .models import RefundStatus
from .payment_gateway import PaymentGateway
from .schemas import (
    BackendRefundRequest,
    RefundApplication,
    RefundListResponse,
    RefundResponse,
    ReviewRequest,
    RetryRequest,
)
from .services import RefundService
from .storage import InMemoryRefundRepository


def create_app(
    repository: InMemoryRefundRepository | None = None,
    gateway: PaymentGateway | None = None,
) -> FastAPI:
    repo = repository or InMemoryRefundRepository()
    gw = gateway or PaymentGateway()
    service = RefundService(repo, gw)

    app = FastAPI(title="Refund Audit Service", version="1.0.0")
    app.state.refund_service = service

    def get_service() -> RefundService:
        return app.state.refund_service

    @app.post(
        "/refunds/user/apply",
        response_model=RefundResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def apply_refund(
        payload: RefundApplication,
        service: RefundService = Depends(get_service),
    ) -> RefundResponse:
        try:
            refund = service.create_user_refund(**payload.model_dump())
            return RefundResponse.model_validate(refund)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post(
        "/refunds/backoffice/create",
        response_model=RefundResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def backoffice_refund(
        payload: BackendRefundRequest,
        service: RefundService = Depends(get_service),
    ) -> RefundResponse:
        try:
            refund = service.create_backend_refund(**payload.model_dump())
            return RefundResponse.model_validate(refund)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @app.post("/refunds/{refund_id}/review", response_model=RefundResponse)
    def review_refund(
        refund_id: str,
        payload: ReviewRequest,
        service: RefundService = Depends(get_service),
    ) -> RefundResponse:
        try:
            refund = service.review_refund(refund_id, **payload.model_dump())
            return RefundResponse.model_validate(refund)
        except InvalidRefundStateError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RefundNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.post("/refunds/{refund_id}/retry", response_model=RefundResponse)
    def retry_refund(
        refund_id: str,
        payload: RetryRequest,
        service: RefundService = Depends(get_service),
    ) -> RefundResponse:
        try:
            refund = service.retry_refund(refund_id, **payload.model_dump())
            return RefundResponse.model_validate(refund)
        except InvalidRefundStateError as exc:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
        except RetryLimitExceededError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
        except RefundNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/refunds/{refund_id}", response_model=RefundResponse)
    def get_refund(refund_id: str, service: RefundService = Depends(get_service)) -> RefundResponse:
        try:
            refund = service.get_refund(refund_id)
            return RefundResponse.model_validate(refund)
        except RefundNotFoundError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    @app.get("/refunds", response_model=RefundListResponse)
    def list_refunds(
        status: RefundStatus | None = None,
        service: RefundService = Depends(get_service),
    ) -> RefundListResponse:
        refunds = service.list_refunds(status=status)
        return RefundListResponse(items=[RefundResponse.model_validate(item) for item in refunds])

    return app


app = create_app()
