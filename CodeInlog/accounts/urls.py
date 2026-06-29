from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('login/', views.user_login, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='logout'),
    path('admin-only/', views.admin_only, name='admin_only'),
    path('class/<int:pk>/', views.class_detail, name='class_detail'),
    path('docent/studenten/', views.teacher_student_management, name='teacher_student_management'),
    path('docent/studenten/<int:pk>/bewerken/', views.teacher_student_edit, name='teacher_student_edit'),
]