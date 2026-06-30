import random
import requests
from django.shortcuts import render
from django.http import JsonResponse
from .models import QuestionAnswer

# URL van de lokale Ollama-server (chat-endpoint, geschikt voor gesprekken
# met geschiedenis, in tegenstelling tot /api/generate dat los van context werkt).
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "jobautomation/openeurollm-dutch"

# Voorbeeldscenario's. Elk scenario is het probleem dat de "klant" (Phi3)
# heeft. De student weet dit nog niet en moet het via vragen achterhalen.
SCENARIOS = [
    """Je laptop kan geen verbinding maken met het wifi-netwerk van school.
Het wifi-icoontje laat een uitroepteken zien. Andere apparaten (je
telefoon) werken wel gewoon op hetzelfde netwerk. Je hebt vanmorgen
een Windows-update geïnstalleerd, daarna begon het probleem.""",

    """Je printer print niets meer af, hoewel het printerlampje aan
staat. Op je scherm krijg je de melding "printer offline". Je hebt
gisteren nog wel kunnen printen. Je weet niet zeker of de printer
nog wel met de USB-kabel verbonden is, of via wifi werkt.""",

    """Outlook geeft steeds een foutmelding bij het versturen van een
e-mail met een bijlage: "Bestand kan niet worden verzonden, probeer
het later opnieuw". Het bestand is een Word-document van ongeveer
25 MB. Kleinere bijlagen verstuur je wel zonder problemen.""",

    """Je kan niet inloggen op je schoolaccount. Je krijgt de melding
"Wachtwoord onjuist", ook al ben je zeker van je wachtwoord. Je hebt
drie dagen geleden je wachtwoord gewijzigd op verzoek van school.
Caps Lock staat uit.""",
]


def home(request):
    """
    Toont de chatbot-pagina (HTML/JS frontend).

    Hoe het werkt: deze view doet niets anders dan het template
    'chatbot/index.html' renderen. Alle logica (gesprek starten, vragen
    stellen, antwoorden tonen) gebeurt in JavaScript in dat template,
    dat de andere views hieronder aanroept via fetch().
    """
    return render(request, 'chatbot/index.html')


def build_system_prompt(scenario):
    """
    Bouwt de "systeeminstructie": de vaste rol en spelregels die Phi3
    gedurende het hele gesprek moet aanhouden.

    Hoe het werkt: dit is één tekst die uitlegt dat Phi3 een klant van
    een IT-helpdesk speelt, met een specifiek (verborgen) probleem.
    Deze instructie wordt als 'system'-bericht meegestuurd bij elk
    verzoek aan Ollama, zodat het model gedurende het hele gesprek in
    karakter blijft en niet meteen de oplossing of oorzaak weggeeft.
    """
    return f"""Je speelt de rol van een klant die belt naar de IT-helpdesk
van een school. Je bent geen IT-expert en gebruikt geen technische
vaktermen, je beschrijft alleen wat je ziet en ervaart.

Dit is jouw situatie (dit weet de helpdeskmedewerker nog niet):
{scenario}

Regels die je ALTIJD moet volgen:
- Jij belt de helpdesk, dus jij begint het gesprek door kort je
  probleem uit te leggen (niet te uitgebreid, een paar zinnes).
- Geef nooit uit jezelf de technische oorzaak of de oplossing weg.
  Beantwoord alleen wat er gevraagd wordt.
- Blijf in karakter als de klant, ook al weet je zelf niet wat de
  technische oorzaak is.
- Reageer kort en natuurlijk, zoals een echte klant aan de telefoon.
- Als de helpdeskmedewerker een oplossing voorstelt die logisch bij
  jouw probleem past, bevestig dan dat het is opgelost. Stelt hij iets
  voor dat niet zou werken, reageer dan alsof het probleem blijft
  bestaan.
- Je bent en blijft de klant. Ga nooit zelf vragen stellen als een
  helpdeskmedewerker."""


def ask_ollama_chat(messages):
    """
    Stuurt de volledige gespreksgeschiedenis naar Phi3 via Ollama's
    /api/chat-endpoint en geeft het nieuwste antwoord terug als tekst.

    Hoe het werkt: 'messages' is een lijst van berichten met een rol
    ('system', 'user' of 'assistant') en inhoud. Door steeds de HELE
    geschiedenis mee te sturen, "onthoudt" Phi3 wat er al besproken is.
    'stream: False' zorgt dat we het volledige antwoord in één keer
    terugkrijgen.

    De timeout staat hoog (180 sec), omdat een lokaal model op een CPU
    soms langzaam is, vooral als de geschiedenis (en dus de prompt)
    langer wordt naarmate het gesprek doorgaat.

    Lukt het verzoek niet, dan wordt de exacte foutmelding meegegeven
    in de response, zodat je in de browser kan zien wat er misging
    (timeout, verbinding weigert, verkeerd modelnaam, etc.) in plaats
    van alleen een generieke melding.
    """
    try:
        response = requests.post(
            OLLAMA_CHAT_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False,
            },
            timeout=180,  # 3 minuten, lokale modellen kunnen traag zijn
        )
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "Sorry, ik kon geen antwoord genereren.").strip()
    except requests.exceptions.Timeout:
        return "Sorry, het AI-model deed er te lang over (timeout). Probeer het opnieuw of gebruik een kleiner scenario."
    except requests.exceptions.ConnectionError:
        return "Sorry, ik kan geen verbinding maken met Ollama. Draait 'ollama serve' nog?"
    except requests.exceptions.RequestException as e:
        return f"Sorry, er ging iets mis met het AI-model: {e}"


def start_chat(request):
    """
    Start een nieuw helpdesk-gesprek: kiest een scenario en laat de
    "klant" (Phi3) als eerste zijn probleem uitleggen.

    Hoe het werkt:
    1. Er wordt willekeurig één scenario uit SCENARIOS gekozen.
    2. Met build_system_prompt() wordt de rol/spelregels-tekst gemaakt.
    3. De geschiedenis begint met alleen dit system-bericht. Omdat de
       klant het gesprek moet beginnen, voegen we daarna een
       instructie-bericht toe ("Begin het gesprek...") om Phi3 een
       eerste antwoord te laten genereren - dit instructiebericht wordt
       NIET opgeslagen in de geschiedenis, want het is geen onderdeel
       van het echte gesprek tussen klant en helpdeskmedewerker.
    4. Het eerste antwoord van Phi3 (de probleemuitleg van de klant)
       wordt wél opgeslagen in de sessie, als 'assistant'-bericht, zodat
       latere vragen van de student hier op kunnen aansluiten.
    5. De volledige geschiedenis (system + eerste klantbericht) wordt
       opgeslagen in request.session, zodat chatbot_response() hierop
       kan verder bouwen.
    """
    scenario = random.choice(SCENARIOS)
    system_prompt = build_system_prompt(scenario)

    kickoff_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "Begin het gesprek door kort je probleem uit te leggen aan de helpdeskmedewerker."},
    ]
    opening_message = ask_ollama_chat(kickoff_messages)

    # De instructie zelf wordt niet bewaard, alleen de systeeminstructie
    # en het eerste echte bericht van de klant.
    request.session['chat_messages'] = [
        {"role": "system", "content": system_prompt},
        {"role": "assistant", "content": opening_message},
    ]

    return JsonResponse({'answer': opening_message})


def chatbot_response(request):
    """
    API-endpoint dat de reactie van de student verwerkt en het antwoord
    van de "klant" (Phi3) teruggeeft.

    Hoe het werkt:
    1. De reactie van de student wordt uit de querystring gehaald
       (?question=...).
    2. De bestaande gespreksgeschiedenis wordt uit de sessie gehaald.
       Is er nog geen gesprek gestart (bv. de pagina is net geopend),
       dan wordt de gebruiker gevraagd om eerst een gesprek te starten.
    3. De reactie van de student wordt toegevoegd aan de geschiedenis
       met rol 'user'.
    4. De hele geschiedenis wordt naar Phi3 gestuurd via
       ask_ollama_chat(), zodat het antwoord aansluit op alles wat er
       al gezegd is.
    5. Het antwoord van Phi3 wordt toegevoegd aan de geschiedenis met
       rol 'assistant', en de bijgewerkte geschiedenis wordt terug in
       de sessie opgeslagen voor de volgende beurt.
    """
    user_input = request.GET.get('question', '').strip()

    if not user_input:
        return JsonResponse({'answer': "Typ eerst een reactie naar de klant."})

    messages = request.session.get('chat_messages')
    if not messages:
        return JsonResponse({'answer': "Er is nog geen gesprek gestart. Vernieuw de pagina om te beginnen."})

    messages.append({"role": "user", "content": user_input})
    answer = ask_ollama_chat(messages)
    messages.append({"role": "assistant", "content": answer})

    request.session['chat_messages'] = messages

    return JsonResponse({'answer': answer})


def reset_scenario(request):
    """
    Beëindigt het huidige gesprek, zodat er bij de volgende keer
    starten een nieuw, willekeurig scenario gekozen wordt.

    Hoe het werkt: verwijdert simpelweg de opgeslagen gespreksgeschiedenis
    uit de sessie. start_chat() begint daarna weer helemaal vers.
    """
    request.session.pop('chat_messages', None)
    return JsonResponse({'status': 'ok', 'message': 'Gesprek gereset. Start een nieuw gesprek.'})