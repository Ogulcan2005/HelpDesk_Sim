from django.urls import path, include
from . import views

urlpatterns = [
    path("", views.home, name="home"),

    path("login/", views.user_login, name="login"),
    path("register/", views.register, name="register"),
    path("logout/", views.user_logout, name="logout"),

    path("class/<int:pk>/", views.class_detail, name="class_detail"),

    path("admin-only/", views.admin_only, name="admin_only"),

    # ✅ ADD THIS LINE
    path("chat/", include("chat.urls")),
]