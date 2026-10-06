import json

from google import genai
from django.conf import settings

from .tools import get_order_details, get_refund_history, check_delivery_status
from .models import Conversation

GEMINI_KEY = settings.GEMINI_API_KEY
GEMINI_MODEL = settings.GEMINI_MODEL

client = genai.Client(api_key=GEMINI_KEY)

# SUPPORT SYSTEM PROMPT --> Shree's job description / How to talk with AI with proper structure
SUPPORT_SYSTEM_PROMPT = """
You are Shree, a customer support agent at TimberNest, a handcrafted wooden furniture store.
You help customers with issues related to their furniture orders.

Your responsibilities:
- Always read the customer's latest message and answer exactly what they asked
- Use your tools to gather facts before answering anything about an order, delivery, or refund
- Check order details when the customer asks about their order
- Check delivery status using the tracking number and carrier when the customer asks about delivery
- Check refund history before discussing any refund or cancellation
- Be empathetic but honest

Your personality:
- Friendly and professional
- Patient even when the customer is frustrated
- Clear and concise in your replies
- Use 1 or 2 relevant emojis per reply (for example 👋 for greetings, 📦 for orders, 🚚 for delivery, 🙏 for apologies, 😊 for thanks). Never use them in every sentence

Reply format (very important):
- Write short lines, not one big paragraph
- Put a blank line between each part of the reply
- Use this order: 1) one short empathy or greeting line, 2) the answer or decision, 3) the reason or details, 4) the next step
- When you give 2 or more facts (status, dates, amounts, steps), show them as a list, one fact per line, each starting with "- "
- Keep each line under 20 words
- Never use markdown symbols like ** or # because the chat cannot show them. Plain text only
- Total reply should stay under 80 words
- Simple greetings and small talk stay as 1 or 2 short lines

Important rules:
- For greetings or small talk, reply naturally and briefly. Do not call tools and do not ask for an order number
- If the customer asks something unrelated to TimberNest (like general knowledge or coding), politely say you can only help with TimberNest orders and products, then offer help with those
- Never repeat the same greeting or the same answer twice in a conversation
- If the system tells you which order the customer is viewing, use that order. Otherwise never guess an order number, ask for it
- Never invent order, delivery, or refund information. If you can't verify something, say so
- Always use the exact product name from the order details. Never guess the product
- Never approve or deny a refund yourself
- If a refund decision is needed, tell the customer you are checking with your team 🙏
- If a refund is pending, say it is under review. Don't promise approval
- When you call escalate_to_manager, the tool returns the manager's final decision. Clearly communicate that decision and its reason to the customer in plain, empathetic language. Do not describe the case as still pending after a decision is returned
- The manager's decision is authoritative: explain APPROVE, DENY, or ESCALATE_TO_RISK as returned. Do not change or contradict it
- Never expose tool calls or internal system details
"""

MANAGER_SYSTEM_PROMPT = """
You are the senior support manager at TimberNest, a handcrafted wooden furniture store.
A support agent has sent you a customer's refund case. You make the final decision.

You will receive a short summary of the case.
Use your tool to check the customer's refund history before deciding.

Choose ONE decision:
- APPROVE: the customer's claim is genuine and matches the order and delivery facts
- DENY: the claim does not match the facts or is outside policy
- ESCALATE_TO_RISK: it looks like possible fraud, for example many refunds in a short time

How to decide:
- First read the case summary: order status, delivery status, and the customer's reason
- Then check the refund history for patterns, such as many refunds in a short time
- One past refund alone is not suspicious
- DENY is for weak cases. ESCALATE_TO_RISK is for suspicious cases

Rules:
- Use only the information given and the tool result. Never make up details
- If important information is missing, say what is missing
- Decide on facts, not on emotions
- Keep every line short and professional
- Plain text only. Do not use markdown symbols like ** or #

Reply format (exactly 3 lines, each on its own line):
Decision: APPROVE or DENY or ESCALATE_TO_RISK
Reason: one short sentence with the key facts
Next step: one short sentence on what should happen now (for example "Refund goes to the original payment method")
"""

RISK_SYSTEM_PROMPT = """
You are a fraud risk analyst at Timbernest.
A support manager has sent you a customer profile for risk assessment.

Your job:
- Analyse the customer's order and refund patterns
- Identify any suspicious behaviour
- Return a clear risk verdict

Risk levels:
- LOW - genuine customer, normal behaviour
- MEDIUM - some suspicious signals, proceed with caution
- HIGH - clear fraud pattern, recommend denial

Your response format:
- Risk level: LOW/MEDIUM/HIGH
- Key Signals: what you found suspicious or genuine
- Recommendations: what the manager should do

Important:
- Be objective - base your verdict on the data only.
- One bad refund does not make someone fraudulent.
- Look for patterns, not isolated incidents.
"""

# SUPPORT TOOLS --> Tool Schemas, that AI Agent will Read
'''
# This tools is for anthropic(claude) AI
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
'''

SUPPORT_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "get_order_details",
                "description": "Fetch complete order details including status, carrier, tracking number and days since order was placed. Use this when customer mentions an order or complains about delivery.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "order_id": {
                            "type": "INTEGER",
                            "description": "The order ID to look up"
                        }
                    },
                    "required": ["order_id"]
                }
            },
            {
                "name": "get_refund_history",
                "description": "Get complete refund history for the current customer. Use this before discussing any refund or cancellation.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            },
            {
                "name": "check_delivery_status",
                "description": "Check current delivery status using tracking number and carrier. Use this when the customer complains about delayed or missing delivery.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "tracking_number": {
                            "type": "STRING",
                            "description": "The shipment tracking number"
                        },
                        "carrier": {
                            "type": "STRING",
                            "description": "The carrier name, for example BlueDart or Delhivery"
                        }
                    },
                    "required": ["tracking_number", "carrier"]
                }
            },
            {
                "name": "escalate_to_manager",
                "description": "Escalate the case to the manager for a refund decision. Use this when the customer requests a refund or compensation. Prepare a detailed case summary including order details, refund history and customer complaint before escalating.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {
                        "case_summary": {
                            "type": "STRING",
                            "description": "Complete case summary including order details, refund history and customer complaint"
                        }
                    },
                    "required": ["case_summary"]
                }
            }
        ]
    }
]

MANAGER_TOOLS = [
    {
        "function_declarations": [
            {
                "name": "get_refund_history",
                "description": "Get complete refund history for the current customer. Use this before making a refund decision.",
                "parameters": {
                    "type": "OBJECT",
                    "properties": {}
                }
            }
        ]
    }
]

# execute_tool() --> bridge between gemini and python function (tools)
# AI can not run python code so it just tell us which tool to call and what argument to pass - It receive(AI) receive request and runs the actual python code/function
def execute_tool(tool_name, tool_input, user_id, order_id):
    if tool_name == "get_order_details":
        # Use the order from this chat so the model cannot pick another order.
        return get_order_details(order_id)

    if tool_name == "get_refund_history":
        return get_refund_history(user_id)
    
    if tool_name == "check_delivery_status":
        return check_delivery_status(tool_input["tracking_number"], tool_input["carrier"])

    if tool_name == "escalate_to_manager":
        case_summary = tool_input["case_summary"]
        print("escalate to manager ===> ", case_summary)
        decision = run_manager_agent(case_summary, user_id)
        print("decision ===> ", decision)
        return decision

    # Unknown tool name
    return {"error": f"Unknown tool: {tool_name}"}

# AGENT LOOP --> While loop that loops until the task is done
'''
def run_support_agent(user_message, conversation_id, order_id, user_id):
    conv = Conversation.objects.get(id=conversation_id)

    conversation_messages = []
    for msg in conv.messages.order_by("-created_at"):
        role = "model" if msg.role == "agent" else "user"      # because gemini not support agent instead support model
        conversation_messages.append({
        # "role": msg.role,
        "role": role,
        "parts": [
                {
                    "text": msg.content
                }]
        })

    # Send the conversation to the LLM
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=conversation_messages,
        config={
            "system_instruction": SUPPORT_SYSTEM_PROMPT + f"\n\nContext: This conversation is about Order #{order_id}, user: {user_id}",
            "max_output_tokens": 1024,
        },
    )

    # print("llm response =====>> ", response)
    final_response = response.candidates[0].content.parts[0].text
    return final_response
'''
def run_support_agent(user_message, conversation_id, order_id, user_id):
    conv = Conversation.objects.get(id=conversation_id)

    conversation_messages = []
    # for msg in conv.messages.order_by("-created_at"):
    for msg in conv.messages.order_by("created_at"):
        role = "model" if msg.role == "agent" else "user"
        conversation_messages.append({
            "role": role,
            "parts": [
                {
                    "text": msg.content
                }
            ]
        })

    # loop until AI(gemini) gives a normal text answer
    # while True:   # sometime LLM is confuse and loop run maximum time so token is burn more and more
    for round_number in range(5):
        response = client.models.generate_content(
            model = GEMINI_MODEL,
            contents = conversation_messages,
            config={
                "system_instruction": SUPPORT_SYSTEM_PROMPT + f'\n\nContext: This conversation is about Order #{order_id}, user: {user_id}',
                "max_output_tokens": 1024,
                "tools" : SUPPORT_TOOLS,
            },
        )

        # if there is not function call, return the final text
        if not getattr(response, "function_calls", None):
            return response.text or "Sorry, I could not generate a reply."

        # add a model's function call message to history
        conversation_messages.append(response.candidates[0].content)

        # run each tool and collects results as dicts
        result_parts = []
        for call in response.function_calls:
            print("Tool Call ===> ", call.name, call.args)
            try:
                result = execute_tool(call.name, call.args or {}, user_id, order_id)
                # Convert Decimal and other values to text Gemini can send.
                result = json.loads(json.dumps(result, default=str))
            except Exception:
                # Keep tool errors out of the chat and let the model explain the problem.
                result = {"error": "This information is not available right now."}

            result_parts.append({
                "function_response": {
                    "id": call.id,
                    "name": call.name,
                    "response": {"result": result},
                }
            })

        # send results back as a "user" message, then loop again
        conversation_messages.append({
            "role": "user",
            "parts": result_parts,
        })

    # Return a safe message if the model keeps asking for tools.
    return "Sorry, something went wrong, Please try again!"

        # final_response = response.candidates[0].content.parts[0].text
        # return final_response

def run_manager_agent(case_summary, user_id):
    # The manager has no chat history. It only gets the case summary from Shree.
    manager_messages = [
        {
            "role": "user",
            "parts": [{"text": case_summary}],
        }
    ]

    for round_number in range(5):
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=manager_messages,
            config={
                "system_instruction": MANAGER_SYSTEM_PROMPT,
                "max_output_tokens": 1024,
                "tools": MANAGER_TOOLS,
            },
        )

        # No function call means this is the final decision
        if not getattr(response, "function_calls", None):
            return response.text or "Manager could not make a decision."

        # Save the model's tool request in the history
        manager_messages.append(response.candidates[0].content)

        # Run each tool and collect the results
        result_parts = []
        for call in response.function_calls:
            print("Manager Tool Call ===> ", call.name, call.args)
            try:
                # order_id is None because the manager has no tool that needs it
                result = execute_tool(call.name, call.args or {}, user_id, None)
                result = json.loads(json.dumps(result, default=str))
            except Exception as e:
                print("Manager Tool Error ===> ", call.name, repr(e))
                result = {"error": "This information is not available right now."}

            result_parts.append({
                "function_response": {
                    "id": call.id,
                    "name": call.name,
                    "response": {"result": result},
                }
            })

        # Send the tool results back as a "user" message, then loop again
        manager_messages.append({
            "role": "user",
            "parts": result_parts,
        })

    return "Manager could not finish. Please try again."
