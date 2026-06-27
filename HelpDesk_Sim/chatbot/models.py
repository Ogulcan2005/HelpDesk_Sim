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
