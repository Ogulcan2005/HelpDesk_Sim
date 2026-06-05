from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render
import json

from .services import generate_ai_response, create_history


def chat_page(request):
    return render(request, "chat/chat.html")


@csrf_exempt
def chat_api(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST only"}, status=405)

    try:
        data = json.loads(request.body)
        message = data.get("message", "")

        if not message:
            return JsonResponse({"error": "Empty message"}, status=400)

        history = request.session.get("history")

        if not history:
            history = create_history()

        history = list(history)

        reply = generate_ai_response(history, message)

        request.session["history"] = history
        request.session.save()

        return JsonResponse({"response": reply})

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
#change to count as commit while waiting on group members too deliver code to work with