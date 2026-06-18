from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from .forms import TeacherAddStudentForm
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


def _register_context(**extra):
    return {
        'class_groups': ClassGroup.objects.order_by('name'),
        **extra,
    }


def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        class_group_id = request.POST.get('class_group')

        form_data = {
            'name': name,
            'email': email,
            'selected_class_group': class_group_id,
        }

        if not name:
            return render(request, 'accounts/register.html', _register_context(
                message='Gebruikersnaam is verplicht',
                **form_data,
            ))

        if password != password2:
            return render(request, 'accounts/register.html', _register_context(
                message='Passwords do not match',
                **form_data,
            ))

        if User.objects.filter(username=email).exists():
            return render(request, 'accounts/register.html', _register_context(
                message='Account already exists',
                **form_data,
            ))

        class_group = ClassGroup.objects.filter(pk=class_group_id).first()
        if class_group is None:
            return render(request, 'accounts/register.html', _register_context(
                message='Kies een geldige klas',
                **form_data,
            ))

        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
            )
            Student.objects.create(
                user=user,
                name=name,
                class_group=class_group,
            )

        return render(request, 'accounts/register.html', _register_context(
            message='Account created!',
        ))

    return render(request, 'accounts/register.html', _register_context())


def _get_user_role(user):
    if user.is_staff:
        return 'Administrator'
    role = profile_role_for_user(user)
    if role == ROLE_STUDENT:
        return 'Leerling'
    if role == ROLE_TEACHER:
        return 'Docent'
    return 'Gebruiker'


def _get_teacher_profile(user):
    return Teacher.objects.filter(user=user).select_related('class_group').first()


def _user_can_access_class(user, class_group):
    if user.is_staff:
        return True
    teacher = _get_teacher_profile(user)
    return teacher is not None and teacher.class_group_id == class_group.pk


@login_required
def home(request):
    teacher = _get_teacher_profile(request.user)
    return render(request, 'accounts/home.html', {
        'role': _get_user_role(request.user),
        'teacher': teacher,
        'teacher_class': teacher.class_group if teacher else None,
    })


@login_required
def class_detail(request, pk):
    group = get_object_or_404(ClassGroup, pk=pk)

    if not _user_can_access_class(request.user, group):
        raise PermissionDenied

    students = group.student_set.select_related('user').order_by('name')
    teacher = getattr(group, 'teacher', None)
    add_form = TeacherAddStudentForm()

    if request.method == 'POST':
        remove_student_id = request.POST.get('remove_student')
        if remove_student_id:
            student = get_object_or_404(Student, pk=remove_student_id, class_group=group)
            student_name = student.name
            with transaction.atomic():
                student.class_group = None
                student.save(update_fields=['class_group'])
            messages.success(request, f'{student_name} is uit {group.name} verwijderd.')
            return redirect('class_detail', pk=group.pk)

        add_form = TeacherAddStudentForm(request.POST)
        if add_form.is_valid():
            with transaction.atomic():
                add_form.save(class_group=group)
            messages.success(request, f'{add_form.cleaned_data["name"]} is toegevoegd aan {group.name}.')
            return redirect('class_detail', pk=group.pk)

    return render(request, 'accounts/class_detail.html', {
        'group': group,
        'students': students,
        'teacher': teacher,
        'add_form': add_form,
        'can_add_students': _get_teacher_profile(request.user) is not None or request.user.is_staff,
    })


def user_logout(request):
    logout(request)
    return redirect('login')


@staff_member_required
def admin_only(request):
    return render(request, 'accounts/admin_only.html')