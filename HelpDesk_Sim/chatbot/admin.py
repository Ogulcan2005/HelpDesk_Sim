from django.contrib import admin
from django.utils.html import escape
from django.utils.safestring import mark_safe
from .models import QuestionAnswer, ChatLog

# Registreert QuestionAnswer in de Django admin, zodat FAQ-vragen en
# -antwoorden via het admin-paneel beheerd (toegevoegd/bewerkt/verwijderd)
# kunnen worden, in plaats van rechtstreeks in de database.
admin.site.register(QuestionAnswer)


@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    """
    Admin-configuratie voor opgeslagen helpdesk-gesprekken.

    Hoe het werkt: 'conversation' bevat de ruwe data (JSON) - dat blijft
    de beste manier om dit op te slaan in de database. Voor het
    BEKIJKEN in de admin tonen we echter 'transcript': een opgemaakte,
    leesbare versie daarvan (zie transcript() hieronder). De ruwe JSON
    wordt verborgen via 'exclude', zodat je in de admin alleen de
    leesbare versie ziet.

    Alle velden staan op read-only, omdat een gesprek niet handmatig
    bewerkt zou moeten worden - het wordt altijd automatisch
    overschreven via de "Gesprek beëindigen"-knop in de chatbot (zie
    chatbot/views.py -> end_chat()).
    """
    list_display = ('user', 'ended_at')
    readonly_fields = ('user', 'transcript', 'ended_at')
    exclude = ('conversation',)

    def has_add_permission(self, request):
        # Voorkomt dat er handmatig nieuwe ChatLogs aangemaakt worden
        # via de admin: deze ontstaan alleen via een echt afgerond gesprek.
        return False

    @admin.display(description='Gesprek')
    def transcript(self, obj):
        """
        Zet de ruwe JSON-lijst van berichten om naar een leesbare,
        opgemaakte gesprekstranscript voor de admin-detailpagina.

        Hoe het werkt:
        1. Loopt door 'obj.conversation' (de lijst met berichten).
        2. Het 'system'-bericht (de instructie/spelregels voor het
           model) wordt overgeslagen, want dat is geen onderdeel van
           het echte gesprek en alleen ruis voor wie het wil naleest.
        3. 'assistant'-berichten (de klant/het AI-model) en
           'user'-berichten (de student) krijgen ieder een eigen label
           en kleur, met daaronder de tekst van het bericht.
        4. escape() voorkomt dat tekst uit het gesprek per ongeluk als
           HTML geïnterpreteerd wordt (bv. als iemand "<b>" zou typen).
        5. mark_safe() geeft aan dat de samengestelde HTML-string veilig
           is om te tonen zonder verdere escaping door Django - dat mag
           hier omdat elk los stukje tekst (label en content) al apart
           door escape() is gehaald, vóórdat het werd samengevoegd.
        """
        conversation = obj.conversation or []
        rows = []
        for message in conversation:
            role = message.get('role')
            content = message.get('content', '')

            if role == 'system':
                continue
            elif role == 'assistant':
                label, color = 'Klant', '#555'
            elif role == 'user':
                label, color = 'Student', '#0b5ed7'
            else:
                label, color = role, '#000'

            rows.append(
                f'<p style="margin:4px 0;"><strong style="color:{color};">{escape(label)}:</strong> {escape(content)}</p>'
            )

        if not rows:
            return "Geen gesprek beschikbaar."

        return mark_safe(''.join(rows))
