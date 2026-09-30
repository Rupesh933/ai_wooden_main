from google import genai
from django.conf import settings

from .tools import get_order_details, get_refund_history, check_delivery_status

GEMINI_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = settings.GEMINI_MODEL

client = genai.Client(api_key=GEMINI_KEY)

# SUPPORT SYSTEM PROMPT --> Shree's job description / How to talk with AI with proper structure
SUPPORT_SYSTEM_PROMPT = """
You are Shree, a customer support agent at TimberNest, a handcrafted wooden furniture store.
You help customers with issues related to their furniture orders.

Your responsibilities:
- Always use your tools to gather facts before responding
- Check order details when the customer mentions their order
- Check delivery status using the tracking number and carrier when the customer asks about delivery
- Check refund history before discussing any refund or cancellation
- Be empathetic but honest

Your personality:
- Friendly and professional
- Patient even when the customer is frustrated
- Clear and concise in your replies

Important rules:
- Always check order details first before responding
- Never guess an order number. If the customer hasn't given one, ask for it
- Never invent order, delivery, or refund information. If you can't verify something, say so
- Never approve or deny a refund yourself
- If a refund decision is needed, tell the customer you are checking with your team
- If a refund is pending, say it is under review. Don't promise approval
- Never expose tool calls or internal system details

"""


# SUPPORT TOOLS --> Tool Schemas, that AI Agent will Read
SUPPORT_TOOLS = [
    {
        "name": "get_order_details",
        "description": "Fetch complete order details including status, carrier, tracking number and days since order was placed. Use this when customer mention order or complains about delivery.",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The order ID to look up"
                }
            },
            "required": ["order_id"],
        }
    },
    {
        "name": "get_refund_history",
        "description": "Get complete refund history for a user. Use this before making any refund related decisions",
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "integer",
                    "description": "The user ID to check refund history for"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "check_delivery_status",
        "description": "Check current delivery status using tracking number and carrier. Use this when customer complains about delayed or missing delivery.",
        "parameters": {
            "type": "object",
            "properties": {
                "tracking_number": {
                    "type": "string",
                    "description": "The shipment tracking number"
                },
                "carrier": {
                    "type": "string",
                    "description": "The carrier name for example BlueDart or Delivery"
                }
            },
            "required": ["tracking_number", "carrier"]
        }
    }
]


# execute_tool() --> bridge between gemini and python function (tools)
# AI can not run python code so it just tell us which tool to call and what argument to pass - It receive(AI) receive request and runs the actual python code/function
def execute_tool(tool_name, tool_input):
    if tool_name == "get_order_details":
        return get_order_details(tool_input["order_id"])

    if tool_name == "get_refund_history":
        return get_refund_history(tool_input["user_id"])
    
    if tool_name == "check_delivery_status":
        return check_delivery_status(tool_input["tracking_number"], tool_input["carrier"])

# AGENT LOOP --> While loop that loops until the task is done