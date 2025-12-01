from fastapi.testclient import TestClient

from app.main import create_app
from app.payment_gateway import PaymentResult
from app.storage import InMemoryRefundRepository


class FlakyGateway:
    def __init__(self) -> None:
        self.calls = 0

    def process_refund(self, refund):  # noqa: D401 - signature defined by service
        self.calls += 1
        if self.calls == 1:
            return PaymentResult(success=False, code="GATEWAY_DOWN", message="temporary outage")
        return PaymentResult(success=True, code="SUCCESS", message="refunded")


def test_user_refund_happy_path():
    client = TestClient(create_app())

    apply_payload = {
        "order_id": "ORD-1",
        "user_id": "U-1",
        "amount": "99.50",
        "reason": "duplicate order",
    }
    apply_resp = client.post("/refunds/user/apply", json=apply_payload)
    assert apply_resp.status_code == 201
    refund_id = apply_resp.json()["id"]
    assert apply_resp.json()["status"] == "PENDING_REVIEW"

    review_payload = {"approve": True, "operator_id": "admin", "audit_notes": "looks good"}
    review_resp = client.post(f"/refunds/{refund_id}/review", json=review_payload)
    assert review_resp.status_code == 200
    body = review_resp.json()
    assert body["status"] == "REFUNDED"
    assert body["remote_attempt_count"] == 1
    assert body["failure_reason"] is None

    get_resp = client.get(f"/refunds/{refund_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["status"] == "REFUNDED"


def test_retry_flow_after_gateway_failure():
    repo = InMemoryRefundRepository()
    gateway = FlakyGateway()
    client = TestClient(create_app(repository=repo, gateway=gateway))

    apply_resp = client.post(
        "/refunds/user/apply",
        json={
            "order_id": "ORD-RETRY",
            "user_id": "U-RET",
            "amount": "50.00",
            "reason": "service error",
        },
    )
    refund_id = apply_resp.json()["id"]

    review_resp = client.post(
        f"/refunds/{refund_id}/review",
        json={"approve": True, "operator_id": "ops", "audit_notes": "first try"},
    )
    assert review_resp.status_code == 200
    assert review_resp.json()["status"] == "REFUND_FAILED"
    assert review_resp.json()["remote_attempt_count"] == 1
    assert review_resp.json()["failure_reason"] == "temporary outage"

    retry_resp = client.post(
        f"/refunds/{refund_id}/retry",
        json={"operator_id": "ops", "audit_notes": "manual retry"},
    )
    assert retry_resp.status_code == 200
    assert retry_resp.json()["status"] == "REFUNDED"
    assert retry_resp.json()["manual_retry_count"] == 1
    assert retry_resp.json()["remote_attempt_count"] == 2


def test_backoffice_can_issue_refund_without_review():
    client = TestClient(create_app())

    payload = {
        "order_id": "ORD-ADMIN",
        "user_id": "U-BO",
        "amount": "20.00",
        "reason": "manual adjustment",
        "operator_id": "finance",
        "audit_notes": "ex gratia",
    }
    resp = client.post("/refunds/backoffice/create", json=payload)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "REFUNDED"
    assert body["source"] == "BACKOFFICE"
    assert body["remote_attempt_count"] == 1
