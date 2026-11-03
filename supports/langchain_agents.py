from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain_tools import get_order_details, get_refund_history, check_delivery_status, search_knowledge_base
from agents import SUPPORT_SYSTEM_PROMPT
from langgraph.checkpoint.memory import InMemorySaver


llm = ChatGoogleGenerativeAI(
    model = settings.GEMINI_MODEL,
    api_key = settings.GEMINI_API_KEY
)

SUPPORT_TOOLS = [get_order_details, get_refund_history, check_delivery_status, search_knowledge_base]

checkpointer = InMemorySaver()

support_agent = create_agent(
    model = llm,
    tools = SUPPORT_TOOLS,
    system_prompt=SUPPORT_SYSTEM_PROMPT,
    checkpointer=checkpointer    # provide conversation history
)