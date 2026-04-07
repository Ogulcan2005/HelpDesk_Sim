from django.shortcuts import render
from django.http import JsonResponse
from .models import QuestionAnswer

# Home page view toont de HTML frontend
def home(request):
    return render(request, 'chatbot/index.html')

def login(request):
    return render(request, 'inlogpage/index.html')

# Chatbot API view haalt antwoord uit database
def chatbot_response(request):
    # Haal de vraag van de gebruiker op uit de URL
    user_input = request.GET.get('question', '').lower()

    # Loop door alle vragen in de database
    # zoekt de keyword van je zin of die in de database staat
    for q_answer in QuestionAnswer.objects.all():
        if q_answer.question.lower() in user_input:
            return JsonResponse({'answer': q_answer.answer})

    # Als er geen match is
    return JsonResponse({'answer': "Sorry, ik begrijp je vraag niet."})