from orders.models import Order, RefundRequest
from django.utils import timezone
from .tracking_data import DELIVERY_DATA

from datetime import timedelta

def get_order_details(order_id):
    try:
        order = Order.objects.get(id=order_id)
        return {
            "order_id": order.id,
            "product_name": order.product_name,
            "amount": order.amount,
            "status": order.status,
            "carrier": order.carrier,
            "tracking_number": order.tracking_number,
            "delivery_address": order.delivery,
            "ordered_on": order.created_at.strftime("%d %b %Y"), # 25 may 2026
            "days_since_order": (timezone.now() - order.created_at).days  # 20
        }
    except Order.DoesNotExist:
        return {"error": f"Order #{order.id} not found."}


def get_refund_history(order_id=None, user_id=None):
    if order_id is not None:
        refunds = RefundRequest.objects.filter(order_id=order_id).order_by("-created_at")
    elif user_id is not None:
        refunds = RefundRequest.objects.filter(user_id=user_id).order_by("-created_at")
    else:
        return {"total_refund_request": 0, "history": []}

    history = []
    for refund in refunds:
        history.append({
            "order_id": refund.order.id,
            "product": refund.order.product_name,
            "reason": refund.reason,
            "status": refund.status,
            "requested_on": refund.created_at.strftime("%d %b %Y"),
        })
    return {
        "total_refund_request": len(history),
        "history": history
    }

def check_delivery_status(tracking_number, carrier):
    default_response = {
        "status": "Unknown",
        "last_location": "Tracking info unavailable",
        "last_update": "N/A",
        "estimated_delivery": "Contact carrier directly",
        "delay_reason": "No update for carrier",
    }

    result = DELIVERY_DATA.get(tracking_number, default_response)
    result["tracking_number"] = tracking_number
    result["carrier"] = carrier
    return result

def get_customer_risk_profile(user_id):
    refunds = RefundRequest.objects.filter(user_id=user_id)
    orders = Order.objects.filter(user_id=user_id)

    # recent 90 days refund request
    recent_refunds_request = refunds.filter(created_at__gte=timezone.now() - timedelta(days=90)).count()

    denied = refunds.filter(status="denied").count()
    approved = refunds.filter(status="approved")
    pending = refunds.filter(status="pending")

    total_orders = orders.count()
    total_refunds = refunds.count()

    if total_orders > 0:
        refund_to_order_reatio = round(total_refunds / total_orders, 2)  # order = 8, refund = 6
    else:
        refund_to_order_reatio = 0

    return {
        "user_id": user_id,
        "total_orders": total_orders,
        "recent_refunds_request": recent_refunds_request,
        "refund_last_90_days": total_refunds,
        "denied_refunds": denied,
        "approved_refunds": approved,
        "pending_refunds": pending,
        "refund_to_order_ratio": refund_to_order_reatio
    }