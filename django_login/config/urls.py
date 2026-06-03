from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [

    path('admin/', admin.site.urls),



    path('accounts/', include('accounts.urls')),
    path('chat/', include('chat.urls')),



    # password resetting

    path(
        'reset_password/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html'
        ),
        name='password_reset'
    ),

    path(
        'reset_password_sent/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_sent.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_form.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset_password_complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_complete'
    ),
]