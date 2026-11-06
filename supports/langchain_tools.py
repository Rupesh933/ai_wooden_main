from langchain.tools import tool
from .tools import (
    get_order_details as _get_order_details,
    get_refund_history as _get_refund_history,
    check_delivery_status as _check_delivery_status,
    get_customer_risk_profile as _get_customer_risk_profile,
    search_knowledge_base as _search_knowledge_base
)


@tool
def get_order_details(order_id: int) -> dict:
    """Fetch complete order details including status, carrier, tracking number and days since order was placed. Use this when customer mentions an order or complains about delivery."""
    return _get_order_details(order_id)

@tool
def get_refund_history(order_id: int = None, user_id: int = None) -> dict:
    """Get complete refund history for the current customer. Use this before discussing any refund or cancellation."""
    return _get_refund_history(order_id=order_id, user_id=user_id)

@tool
def check_delivery_status(tracking_number: str, carrier: str) -> dict:
    """Check current delivery status using tracking number and carrier. Use this when the customer complains about delayed or missing delivery."""
    return _check_delivery_status(tracking_number, carrier)

@tool
def search_knowledge_base(query: str) -> dict:
    """Search Timbernest company documents including refund policy, warranty policy, and product FAQs. Use this when customer asks about company policies, warranty coverage, warranty claims, refund eligibility, or any general product information that requires accurate company documents."""
    return _search_knowledge_base(query)