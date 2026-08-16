"""Mock MCP tool implementations (hardcoded fake data)."""

from uuid import uuid4

MOCK_ORDERS: dict[str, dict] = {
    "1234": {
        "order_id": "1234",
        "status": "shipped",
        "carrier": "UPS",
        "tracking": "1Z999AA10123456784",
        "eta": "Aug 18, 2026",
    },
    "5678": {
        "order_id": "5678",
        "status": "processing",
        "eta": "Aug 20, 2026",
    },
    "9012": {
        "order_id": "9012",
        "status": "delivered",
        "delivered_on": "Aug 12, 2026",
    },
}


def check_order_status(order_id: str) -> dict:
    """Return the mock status for *order_id*."""
    return MOCK_ORDERS.get(
        order_id,
        {"order_id": order_id, "status": "not_found", "message": "No order found with that ID."},
    )


def create_ticket(issue: str) -> dict:
    """Create a mock support ticket for *issue*."""
    ticket_id = f"TKT-{uuid4().hex[:6].upper()}"
    return {"ticket_id": ticket_id, "status": "open", "issue": issue}
