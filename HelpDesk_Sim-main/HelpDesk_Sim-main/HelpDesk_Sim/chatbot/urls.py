from django.urls import path
from .views import home, start_chat, chatbot_response, reset_scenario

# Deze urlpatterns worden in config/urls.py onder het voorvoegsel
# 'chatbot/' gehangen. Daardoor wordt de pagina hieronder bereikbaar op
# /chatbot/ en de API's op /chatbot/start/, /chatbot/ask/ en
# /chatbot/reset/.
urlpatterns = [
    path('', home, name='chatbot_home'),                 # frontend pagina van de chatbot
    path('start/', start_chat, name='chatbot_start'),     # start een nieuw gesprek/scenario
    path('ask/', chatbot_response, name='chatbot_ask'),   # stuur een reactie naar de klant
    path('reset/', reset_scenario, name='chatbot_reset'), # beëindig het huidige gesprek
]