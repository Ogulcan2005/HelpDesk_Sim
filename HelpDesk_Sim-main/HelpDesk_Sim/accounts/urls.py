"""
URL-configuratie van de accounts-app.

Deze paden worden in config/urls.py op de root ('') ingeplakt, dus de
paden hieronder zijn ook de uiteindelijke URL's in de browser.

Overzicht:
    /                           → home (startpagina na inloggen)
    /login/                     → inlogformulier
    /register/                  → registratie voor nieuwe leerlingen
    /logout/                    → uitloggen
    /admin-only/                → voorbeeldpagina alleen voor staff/admins
    /class/<id>/                → detailpagina van één klas
    /docent/studenten/          → docent: studenten overzicht + aanmaken
    /docent/studenten/<id>/bewerken/ → docent: één student bewerken
"""
from django.urls import path
from . import views

urlpatterns = [
    # Startpagina voor ingelogde gebruikers (rol, docent-links, uitloggen)
    path('', views.home, name='home'),

    # Inloggen met e-mail + wachtwoord
    path('login/', views.user_login, name='login'),

    # Zelf registreren als leerling (voornaam, achternaam, klas kiezen)
    path('register/', views.register, name='register'),

    # Sessie beëindigen en terug naar login
    path('logout/', views.user_logout, name='logout'),

    # Testpagina die alleen bereikbaar is voor is_staff=True gebruikers
    path('admin-only/', views.admin_only, name='admin_only'),

    # Klas bekijken; docenten/staff kunnen studenten toevoegen/verwijderen
    path('class/<int:pk>/', views.class_detail, name='class_detail'),

    # Docentenbeheer: lijst van alle studenten, aanmaken en verwijderen
    path('docent/studenten/', views.teacher_student_management, name='teacher_student_management'),

    # Docentenbeheer: gegevens van één student wijzigen
    path('docent/studenten/<int:pk>/bewerken/', views.teacher_student_edit, name='teacher_student_edit'),
]
