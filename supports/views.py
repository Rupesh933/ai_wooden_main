from django.shortcuts import render
import json
from django.http import JsonResponse
import time

# Create your views here.

def chat(request, order_id):
    if request.method == "POST":
        data = json.loads(request.body)
        user_message = data.get('message')

        if not user_message:
            return JsonResponse({"error": "Empty message"}, status=400)

        print("User Message ===> ", user_message)
        
        time.sleep(5)
        return JsonResponse({"reply": "reply from backend"})