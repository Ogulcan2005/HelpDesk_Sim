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
    """
    Verwerkt het inlogformulier.

    Hoe het werkt:
    - GET-verzoek: toont gewoon het lege inlogformulier.
    - POST-verzoek: haalt e-mail/wachtwoord uit het formulier, en
      gebruikt Django's authenticate() om te checken of dit een geldig
      account is. Klopt het, dan wordt de gebruiker ingelogd (login())
      en doorgestuurd naar de homepagina. Klopt het niet, dan wordt
      hetzelfde formulier opnieuw getoond met een foutmelding.
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


def register(request):
    """
    Verwerkt het registratieformulier voor nieuwe leerlingen.

    Hoe het werkt:
    - GET-verzoek: toont het lege registratieformulier.
    - POST-verzoek:
        1. Controleert dat de twee ingevulde wachtwoorden gelijk zijn.
        2. Controleert dat er nog geen account met dit e-mailadres bestaat.
        3. Maakt, als alles klopt, in één transactie (transaction.atomic,
           dus alles-of-niets) een nieuw User-account én een bijbehorend
           Student-profiel aan. De naam van de leerling wordt afgeleid
           van het e-mailadres (het stuk vóór de @).
    Nieuwe accounts worden hier altijd als leerling (Student) aangemaakt;
    een docentaccount kan alleen via de Django-admin gemaakt worden.
    """
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
    """
    Helperfunctie die de leesbare rolnaam van een gebruiker bepaalt,
    voor weergave op de homepagina.

    Hoe het werkt: staff-gebruikers (is_staff=True, bv. via de admin
    aangemaakt) worden altijd als 'Administrator' getoond. Anders wordt
    gekeken of er een Student- of Teacher-profiel bestaat. Is er geen
    van beide, dan krijgt de gebruiker de algemene rol 'Gebruiker'.
    """
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
    """
    Toont de homepagina voor ingelogde gebruikers, met daarop hun rol.

    Hoe het werkt: de @login_required-decorator stuurt niet-ingelogde
    bezoekers automatisch door naar de loginpagina (zie LOGIN_URL in
    settings.py). Is de gebruiker wel ingelogd, dan wordt zijn/haar rol
    bepaald via _get_user_role() en doorgegeven aan het template.
    """
    return render(request, 'accounts/home.html', {
        'role': _get_user_role(request.user),
    })


@login_required
def class_detail(request, pk):
    """
    Toont de details van één klas: welke leerlingen en docenten erbij horen.

    Hoe het werkt: 'pk' (primary key/ID van de klas) komt uit de URL,
    bijvoorbeeld /class/3/. Daarmee wordt de juiste ClassGroup opgehaald,
    en via de omgekeerde relaties (student_set / teacher_set) worden
    alle leerlingen en docenten van die klas verzameld voor het template.
    """
    group = ClassGroup.objects.get(pk=pk)

    students = group.student_set.all()
    teachers = group.teacher_set.all()

    return render(request, 'accounts/class_detail.html', {
        'group': group,
        'students': students,
        'teachers': teachers
    })


def user_logout(request):
    """
    Logt de huidige gebruiker uit en stuurt terug naar de loginpagina.

    Hoe het werkt: Django's logout() ruimt de sessie van de gebruiker op,
    waarna redirect('login') de browser naar de inlogpagina stuurt.
    """
    logout(request)
    return redirect('login')


@staff_member_required
def admin_only(request):
    """
    Voorbeeldpagina die alleen toegankelijk is voor staff-gebruikers.

    Hoe het werkt: de @staff_member_required-decorator controleert of
    de ingelogde gebruiker is_staff=True heeft. Is dat niet het geval,
    dan wordt de gebruiker automatisch doorgestuurd (naar de admin-login).
    """
    return render(request, 'accounts/admin_only.html')
