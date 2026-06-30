"""
Views (pagina-logica) voor inloggen, registratie, home en docentbeheer.

Elke functie hier hoort bij één URL in urls.py. Django roept de juiste
view aan op basis van het pad in de browser.

Rechten:
    - @login_required     → alleen ingelogde gebruikers
    - @staff_member_required → alleen admin/staff (is_staff=True)
    - PermissionDenied    → docent/staff-checks in class_detail en docent-views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from .forms import TeacherAddStudentForm, TeacherCreateStudentForm, TeacherEditStudentForm
from .models import ClassGroup, Student, Teacher
from .role_utils import ROLE_STUDENT, ROLE_TEACHER, profile_role_for_user


def user_login(request):
    """
    Inlogpagina (/login/).

    POST: e-mail + wachtwoord controleren via authenticate(), bij succes
    inloggen en doorsturen naar home. Bij fout opnieuw formulier tonen.
    GET: leeg inlogformulier tonen.
    """
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
    """Gedeelde template-data voor het registratieformulier (klaslijst + fouten)."""
    return {
        'class_groups': ClassGroup.objects.order_by('name'),
        **extra,
    }


def register(request):
    """
    Registratiepagina (/register/) voor nieuwe leerlingen.

    Valideert voornaam, achternaam, wachtwoord, e-mail en klaskeuze.
    Maakt in één transactie een User + Student-profiel aan.
    Docentaccounts kunnen alleen via de admin aangemaakt worden.
    """
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        class_group_id = request.POST.get('class_group')

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'selected_class_group': class_group_id,
        }

        if not first_name:
            return render(request, 'accounts/register.html', _register_context(
                message='Voornaam is verplicht',
                **form_data,
            ))

        if not last_name:
            return render(request, 'accounts/register.html', _register_context(
                message='Achternaam is verplicht',
                **form_data,
            ))

        if password != password2:
            return render(request, 'accounts/register.html', _register_context(
                message='Wachtwoorden komen niet overeen',
                **form_data,
            ))

        if User.objects.filter(username=email).exists():
            return render(request, 'accounts/register.html', _register_context(
                message='Er bestaat al een account met dit e-mailadres',
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
                first_name=first_name,
                last_name=last_name,
            )
            Student.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                class_group=class_group,
            )

        return render(request, 'accounts/register.html', _register_context(
            message='Account aangemaakt!',
        ))

    return render(request, 'accounts/register.html', _register_context())


def _get_user_role(user):
    """
    Leesbare rolnaam voor op de homepagina.

    Staff → Administrator, anders Leerling/Docent op basis van profiel.
    """
    if user.is_staff:
        return 'Administrator'
    role = profile_role_for_user(user)
    if role == ROLE_STUDENT:
        return 'Leerling'
    if role == ROLE_TEACHER:
        return 'Docent'
    return 'Gebruiker'


def _get_teacher_profile(user):
    """Haalt het Teacher-profiel op van een ingelogde gebruiker (of None)."""
    return Teacher.objects.filter(user=user).select_related('class_group').first()


def _user_can_access_class(user, class_group):
    """
    Mag deze gebruiker de klasdetailpagina bekijken?

    Staff mag alles; docenten alleen hun eigen klas.
    """
    if user.is_staff:
        return True
    teacher = _get_teacher_profile(user)
    return teacher is not None and teacher.class_group_id == class_group.pk


def _user_can_manage_students(user):
    """
    Mag deze gebruiker studenten aanmaken, bewerken of verwijderen?

    Staff en docenten mogen dit; leerlingen niet.
    """
    if user.is_staff:
        return True
    return _get_teacher_profile(user) is not None


@login_required
def home(request):
    """
    Startpagina (/) na inloggen.

    Toont welkomsttekst, rol, en voor docenten links naar hun klas
    en het studentenbeheer.
    """
    teacher = _get_teacher_profile(request.user)
    return render(request, 'accounts/home.html', {
        'role': _get_user_role(request.user),
        'teacher': teacher,
        'teacher_class': teacher.class_group if teacher else None,
    })


@login_required
def class_detail(request, pk):
    """
    Detailpagina van één klas (/class/<id>/).

    Toont docent en studentenlijst. Docenten/staff kunnen via POST:
    - studenten toevoegen (TeacherAddStudentForm)
    - studenten uit de klas verwijderen (account blijft bestaan)
    """
    group = get_object_or_404(ClassGroup, pk=pk)

    if not _user_can_access_class(request.user, group):
        raise PermissionDenied

    students = group.student_set.select_related('user').order_by('last_name', 'first_name')
    teacher = getattr(group, 'teacher', None)
    add_form = TeacherAddStudentForm()

    if request.method == 'POST':
        remove_student_id = request.POST.get('remove_student')
        if remove_student_id:
            student = get_object_or_404(Student, pk=remove_student_id, class_group=group)
            student_name = student.full_name
            with transaction.atomic():
                student.class_group = None
                student.save(update_fields=['class_group'])
            messages.success(request, f'{student_name} is uit {group.name} verwijderd.')
            return redirect('class_detail', pk=group.pk)

        add_form = TeacherAddStudentForm(request.POST)
        if add_form.is_valid():
            with transaction.atomic():
                add_form.save(class_group=group)
            messages.success(request, f'{add_form.full_name} is toegevoegd aan {group.name}.')
            return redirect('class_detail', pk=group.pk)

    return render(request, 'accounts/class_detail.html', {
        'group': group,
        'students': students,
        'teacher': teacher,
        'add_form': add_form,
        'can_add_students': _user_can_manage_students(request.user),
    })


@login_required
def teacher_student_management(request):
    """
    Docentenbeheer (/docent/studenten/).

    Overzicht van alle studenten. Via POST:
    - nieuw studentaccount aanmaken (TeacherCreateStudentForm)
    - bestaand account permanent verwijderen (User + profiel)
    """
    if not _user_can_manage_students(request.user):
        raise PermissionDenied

    students = Student.objects.select_related('user', 'class_group').order_by('last_name', 'first_name')
    form = TeacherCreateStudentForm()

    if request.method == 'POST':
        delete_student_id = request.POST.get('delete_student')
        if delete_student_id:
            student = get_object_or_404(Student, pk=delete_student_id)
            student_name = student.full_name
            with transaction.atomic():
                user = student.user
                if user:
                    user.delete()
                else:
                    student.delete()
            messages.success(request, f'Account van {student_name} is verwijderd.')
            return redirect('teacher_student_management')

        form = TeacherCreateStudentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            class_name = form.cleaned_data['class_group'].name
            messages.success(
                request,
                f'{form.full_name} is aangemaakt en toegevoegd aan {class_name}.',
            )
            return redirect('teacher_student_management')

    return render(request, 'accounts/teacher_students.html', {
        'form': form,
        'students': students,
    })


@login_required
def teacher_student_edit(request, pk):
    """
    Één student bewerken (/docent/studenten/<id>/bewerken/).

    Wijzigt naam, e-mail, wachtwoord en klas via TeacherEditStudentForm.
    """
    if not _user_can_manage_students(request.user):
        raise PermissionDenied

    student = get_object_or_404(Student.objects.select_related('user', 'class_group'), pk=pk)
    form = TeacherEditStudentForm(instance=student)

    if request.method == 'POST':
        form = TeacherEditStudentForm(request.POST, instance=student)
        if form.is_valid():
            with transaction.atomic():
                form.save()
            messages.success(request, f'Account van {student.full_name} is bijgewerkt.')
            return redirect('teacher_student_management')

    return render(request, 'accounts/teacher_student_edit.html', {
        'form': form,
        'student': student,
    })


def user_logout(request):
    """Uitloggen (/logout/): sessie wissen en terug naar login."""
    logout(request)
    return redirect('login')


@staff_member_required
def admin_only(request):
    """
    Voorbeeldpagina (/admin-only/) alleen voor staff-gebruikers.

    Gebruikt @staff_member_required: niet-staff wordt doorgestuurd.
    """
    return render(request, 'accounts/admin_only.html')
