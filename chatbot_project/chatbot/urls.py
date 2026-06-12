from django.urls import path
from .views import home, chatbot_response

urlpatterns = [
    path('', home, name='home'),          # frontend pagina
    path('chatbot/', chatbot_response),   # API endpoint
]
# fixed kunnen laden van code voor login nog niet de chatbot