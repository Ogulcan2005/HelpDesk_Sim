from django.urls import path
from . import views

# Url's van de accounts-app. Deze worden in config/urls.py op de root
# ('') ingeplakt, dus de paden hieronder zijn ook de uiteindelijke
# paden die de gebruiker in de browser ziet (bv. /login/, /register/).
urlpatterns = [
    path('', views.home, name='home'),                       # ingelogde startpagina

    path('login/', views.user_login, name='login'),           # inlogformulier
    path('register/', views.register, name='register'),       # registratieformulier
    path('logout/', views.user_logout, name='logout'),        # uitloggen
    path('admin-only/', views.admin_only, name='admin_only'), # pagina enkel voor staff/admins
    path('class/<int:pk>/', views.class_detail, name='class_detail'),  # detailpagina van 1 klas
]
