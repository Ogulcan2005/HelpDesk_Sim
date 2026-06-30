"""
Root URL-configuratie van het samengevoegde project.

Hier worden de URL's van de losse Django-apps (accounts en chatbot)
samengevoegd tot één routeringstabel. Elke 'path(...)' regel koppelt
een stukje URL aan een view, of - met include() - aan de urls.py van
een hele app.
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Django admin-paneel, te bereiken via /admin/
    path('admin/', admin.site.urls),

    # accounts-app verzorgt de hoofdpagina, login, registratie, rollen, etc.
    # Alle url's uit accounts/urls.py worden hier "ingeplakt" op de root ('').
    path('', include('accounts.urls')),

    # chatbot-app wordt onder het pad /chatbot/ gehangen, zodat de
    # 'home'-route van chatbot niet botst met de 'home'-route van accounts.
    # Resultaat: chatbotpagina op /chatbot/ en de API op /chatbot/ask/
    path('chatbot/', include('chatbot.urls')),

    # 🔐 Ingebouwd Django-systeem voor het resetten van een wachtwoord.
    # Dit zijn 4 stappen die de gebruiker doorloopt: aanvragen, bevestiging
    # dat de mail verstuurd is, nieuw wachtwoord invullen via een link met
    # token, en een afrondingspagina.
    path('reset_password/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html'
    ), name='reset_password'),

    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_sent.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='accounts/password_reset_form.html'
    ), name='password_reset_confirm'),

    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_done.html'
    ), name='password_reset_complete'),
]
