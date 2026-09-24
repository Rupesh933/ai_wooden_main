from orders.models import Order
from django.utils import timezone

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