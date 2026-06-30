"""
Hulpfuncties voor rollen (leerling/docent) en profielbeheer.

Gebruikt door forms.py (admin) en views.py (rolweergave op home).
"""
from django.core.exceptions import ValidationError

from .models import Student, Teacher

# Interne waarden voor rollen (gebruikt in formulieren en logica)
ROLE_STUDENT = 'student'
ROLE_TEACHER = 'teacher'

# Keuzelijst voor admin-formulieren: (waarde, leesbare naam)
ROLE_CHOICES = [
    (ROLE_STUDENT, 'Leerling'),
    (ROLE_TEACHER, 'Docent'),
]


def profile_role_for_user(user):
    """
    Bepaalt of een ingelogde gebruiker leerling of docent is.

    Kijkt of er een Student- of Teacher-profiel aan de User gekoppeld is.
    Geen profiel → None (algemene gebruiker zonder rol).
    """
    if user is None:
        return None
    if Student.objects.filter(user=user).exists():
        return ROLE_STUDENT
    if Teacher.objects.filter(user=user).exists():
        return ROLE_TEACHER
    return None


def _validate_teacher_class_group(class_group, user=None):
    """
    Controleert dat een klas niet al een andere docent heeft.

    Bij bewerken van een bestaande docent wordt die docent zelf
    uitgesloten, zodat hij/zij de eigen klas mag behouden.
    """
    if not class_group:
        return
    qs = Teacher.objects.filter(class_group=class_group)
    if user:
        qs = qs.exclude(user=user)
    if qs.exists():
        raise ValidationError(
            {'class_group': 'Deze klas heeft al een docent. Kies een andere klas of verwijder eerst de huidige docent.'}
        )


def save_profile_for_role(*, role, user, first_name, last_name, class_group, existing_instance=None):
    """
    Slaat een account op als Student of Teacher, afhankelijk van de gekozen rol.

    Verwijdert altijd het profiel van de andere rol (iemand is óf leerling
    óf docent). Ondersteunt ook rolwissel bij bewerken in de admin.
    """
    want_student = role == ROLE_STUDENT
    profile_defaults = {
        'first_name': first_name,
        'last_name': last_name,
        'class_group': class_group,
    }

    if existing_instance is not None:
        if isinstance(existing_instance, Student) and want_student:
            existing_instance.user = user
            existing_instance.first_name = first_name
            existing_instance.last_name = last_name
            existing_instance.class_group = class_group
            existing_instance.save()
            Teacher.objects.filter(user=user).delete()
            return existing_instance

        if isinstance(existing_instance, Teacher) and not want_student:
            if class_group:
                _validate_teacher_class_group(class_group, user=user)
            existing_instance.user = user
            existing_instance.first_name = first_name
            existing_instance.last_name = last_name
            existing_instance.class_group = class_group
            existing_instance.save()
            Student.objects.filter(user=user).delete()
            return existing_instance

        old_class_group = existing_instance.class_group
        if isinstance(existing_instance, Student) and not want_student:
            if class_group:
                _validate_teacher_class_group(class_group, user=user)
            existing_instance.delete()
            teacher, _ = Teacher.objects.update_or_create(
                user=user,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'class_group': class_group or old_class_group,
                },
            )
            return teacher

        if isinstance(existing_instance, Teacher) and want_student:
            existing_instance.delete()
            student, _ = Student.objects.update_or_create(
                user=user,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'class_group': class_group or old_class_group,
                },
            )
            return student

    if want_student:
        Teacher.objects.filter(user=user).delete()
        student, _ = Student.objects.update_or_create(
            user=user,
            defaults=profile_defaults,
        )
        return student

    if class_group:
        _validate_teacher_class_group(class_group, user=user)
    Student.objects.filter(user=user).delete()
    teacher, _ = Teacher.objects.update_or_create(
        user=user,
        defaults=profile_defaults,
    )
    return teacher
