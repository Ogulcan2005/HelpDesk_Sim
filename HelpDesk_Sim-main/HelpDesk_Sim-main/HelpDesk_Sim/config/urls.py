"""
Root URL-configuratie van het samengevoegde project.

Hier worden de URL's van de losse Django-apps (accounts en chatbot)
samengevoegd tot één routeringstabel. Elke 'path(...)' regel koppelt
een stukje URL aan een view, of - met include() - aan de urls.py van
een hele app.
"""
from django.contrib import admin
from django.urls import path, include, reverse_lazy
from django.contrib.auth import views as auth_views

from accounts.forms import DutchPasswordResetForm, DutchSetPasswordForm  # NL-formulieren voor wachtwoord reset

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

    # -------------------------------------------------------------------------
    # Wachtwoord vergeten — 4 stappen (Django auth_views, geen eigen views nodig)
    #
    #   Stap 1: /reset_password/              → e-mail invullen
    #   Stap 2: /reset_password_sent/       → "controleer je e-mail"
    #   Stap 3: /reset/<uid>/<token>/       → link uit e-mail, nieuw wachtwoord
    #   Stap 4: /reset_password_complete/     → wachtwoord opgeslagen
    # -------------------------------------------------------------------------

    # Stap 1: formulier + versturen reset-e-mail
    path(
        'reset_password/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            form_class=DutchPasswordResetForm,
            email_template_name='registration/password_reset_email.html',
            subject_template_name='registration/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='reset_password',
    ),

    # Stap 2: bevestiging dat de e-mail is verstuurd
    path(
        'reset_password_sent/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_sent.html',
        ),
        name='password_reset_done',
    ),

    # Stap 3: unieke link uit e-mail (uid + token controleren of link nog geldig is)
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_form.html',
            form_class=DutchSetPasswordForm,
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),

    # Stap 4: wachtwoord succesvol gewijzigd
    path(
        'reset_password_complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_done.html',
        ),
        name='password_reset_complete',
    ),
]
