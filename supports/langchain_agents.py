from django.conf import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from .langchain_tools import get_order_details, get_refund_history, check_delivery_status, search_knowledge_base
from .agents import SUPPORT_SYSTEM_PROMPT
from langgraph.checkpoint.memory import InMemorySaver
from .models import Conversation, AgentLog


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

def run_support_agent_langchain(conversation_id, user_message, order_id, user_id):
    conv = Conversation.objects.get(id=conversation_id)
    config = {"configurable": {"thread_id": str(conversation_id)}}

    contexual_message = f"[Context: This conversation is about Order #{order_id}, user: {user_id}] {user_message}"

    result = support_agent.invoke(
        {"messages": [{"role": "user", "content": contexual_message}]},
        config=config,
    )

    # print("result ===>> ", result)
    # print("result ===>> ", result['messages'][-1].content)

    final_reply = result["messages"][-1].content

    # Save final reply
    AgentLog.objects.create(conversation=conv,event_type="final",message=final_reply,)

    return final_reply

