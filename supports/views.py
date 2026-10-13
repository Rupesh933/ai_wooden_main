from django.shortcuts import render, get_object_or_404
import json
from django.http import JsonResponse
import time

from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone

from orders.models import Order
from .models import Conversation, Message
from .agents import run_support_agent

# Create your views here.

def chat(request, order_id):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get('message')

        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)

        order = get_object_or_404(Order, id=order_id, user=request.user)

        conversation, created = Conversation.objects.get_or_create(user=request.user, order=order)

        Message.objects.create(conversation=conversation, role="user", content=user_message)

        # send user message and conversation to the LLM
        reply = run_support_agent(user_message, conversation.id, order.id, request.user.id)

        # Store the LLM reply
        Message.objects.create(conversation=conversation, role="agent", content=reply)

        print("User Message ===> ", user_message)

        # time.sleep(5)
        return JsonResponse({"reply": reply})

@staff_member_required
def dashboard(request):
    conversations = Conversation.objects.all().order_by("-created_at")
    print("conversation ====>> ", conversations)
    context = {
        "conversations": conversations
    }

    return render(request, "supports/dashboard.html", context)

@staff_member_required
def conversation_detail(request, conversation_id):
    conversations = get_object_or_404(Conversation, id=conversation_id)
    messages = [
        {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "time": timezone.localtime(message.created_at).strftime("%I:%M %p"),
        }
        for message in conversations.messages.order_by("created_at")
    ]
    agentlogs = [
        {
            "id": log.id,
            "event_type": log.event_type,
            "message": log.message,
            "time": timezone.localtime(log.created_at).strftime("%I:%M %p"),
        }
        for log in conversations.agent_log.order_by("created_at")
    ]
    print("conversations ===>> ", conversations)
    print("messages ===>> ", messages)
    print("agentlogs ===>> ", agentlogs)
    context = {
        "conversations": conversations,
        "messages": messages,
        "agentlogs": agentlogs
    }
    return render(request, "supports/conversation_details.html", context)
