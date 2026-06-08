from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db import transaction
from .models import ClassGroup, Student, Teacher
from .role_utils import ROLE_STUDENT, ROLE_TEACHER, profile_role_for_user


def user_login(request):
    if request.method == 'POST':

        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, 'Je bent succesvol ingelogd!')
            return redirect('home')

        else:
            return render(request, 'accounts/login.html', {
                'error': 'Invalid credentials'
            })

    return render(request, 'accounts/login.html')


def register(request):
    if request.method == 'POST':

        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')

        if password != password2:
            return render(request, 'accounts/register.html', {
                'message': 'Passwords do not match'
            })

        if User.objects.filter(username=email).exists():
            return render(request, 'accounts/register.html', {
                'message': 'Account already exists'
            })

        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
            )
            Student.objects.create(
                user=user,
                name=email.split('@')[0] or email,
            )

        return render(request, 'accounts/register.html', {
            'message': 'Account created!'
        })

    return render(request, 'accounts/register.html')


def _get_user_role(user):
    if user.is_staff:
        return 'Administrator'
    role = profile_role_for_user(user)
    if role == ROLE_STUDENT:
        return 'Leerling'
    if role == ROLE_TEACHER:
        return 'Docent'
    return 'Gebruiker'


@login_required
def home(request):
    return render(request, 'accounts/home.html', {
        'role': _get_user_role(request.user),
    })


@login_required
def class_detail(request, pk):
    group = ClassGroup.objects.get(pk=pk)

    students = group.student_set.all()
    teachers = group.teacher_set.all()

    return render(request, 'accounts/class_detail.html', {
        'group': group,
        'students': students,
        'teachers': teachers
    })


def user_logout(request):
    logout(request)
    return redirect('login')


# ✅ NIEUW: admin-only view
@staff_member_required
def admin_only(request):
    return render(request, 'accounts/admin_only.html')