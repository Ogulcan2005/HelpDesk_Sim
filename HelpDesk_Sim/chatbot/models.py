from django.conf import settings
from django.db import models


class QuestionAnswer(models.Model):
    """
    Eén rij in de FAQ-database: een vraag met het bijbehorende antwoord.

    Hoe het werkt: 'question' is een stukje tekst (keyword/zin) waarop
    gezocht wordt, en 'answer' is de tekst die de chatbot teruggeeft
    als die vraag (of een deel ervan) voorkomt in wat de gebruiker
    intypt. Zie chatbot/views.py -> chatbot_response() voor de zoeklogica.
    """
    question = models.CharField(max_length=255)
    answer = models.TextField()

    def __str__(self):
        # Bepaalt hoe een QuestionAnswer-object wordt weergegeven,
        # bijvoorbeeld in de Django admin-lijst. Hier laten we simpelweg
        # de vraag zien zodat je objecten makkelijk herkent.
        return self.question


class ChatLog(models.Model):
    """
    Slaat het laatst afgeronde helpdesk-gesprek van één student op.

    Hoe het werkt: 'user' is een OneToOneField (1-op-1 koppeling). Dat
    betekent dat elke gebruiker maximaal ÉÉN ChatLog-rij kan hebben in
    de database. Wordt een nieuw gesprek opgeslagen, dan wordt de
    bestaande rij overschreven (via update_or_create in de view) in
    plaats van dat er een nieuwe rij bijkomt. Zo blijft de database
    klein: er wordt altijd maar 1 gesprek per student bewaard, namelijk
    het laatst beëindigde gesprek.

    'conversation' is een JSONField: hierin wordt de volledige
    gespreksgeschiedenis bewaard als lijst van berichten, bijvoorbeeld:
        [{"role": "system", "content": "..."},
         {"role": "assistant", "content": "Hallo, ik heb een probleem..."},
         {"role": "user", "content": "Wat zie je op je scherm?"}, ...]
    Dit is de professionele/aanbevolen manier om dit soort
    semi-gestructureerde data (een variabel aantal chatberichten) op te
    slaan, in plaats van bijvoorbeeld elk bericht in een losse rij of
    kolom te proppen.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chat_log',
    )
    conversation = models.JSONField()
    ended_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        # Laat in de admin-lijst zien van wie het gesprek is en wanneer
        # het is opgeslagen, zodat je niet elk gesprek hoeft te openen
        # om te weten waar je naar kijkt.
        return f"Gesprek van {self.user} ({self.ended_at:%d-%m-%Y %H:%M})"
