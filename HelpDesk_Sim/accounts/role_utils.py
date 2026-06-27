from django.core.exceptions import ValidationError

from .models import Student, Teacher

# Interne waarden die de rol van een account aangeven.
ROLE_STUDENT = 'student'
ROLE_TEACHER = 'teacher'

# Keuzelijst die in formulieren wordt gebruikt (waarde, leesbare naam).
ROLE_CHOICES = [
    (ROLE_STUDENT, 'Leerling'),
    (ROLE_TEACHER, 'Docent'),
]


def profile_role_for_user(user):
    """
    Zoekt uit of een gebruiker een Student- of Teacher-profiel heeft.

    Hoe het werkt: er wordt simpelweg gecheckt of er een Student-record
    of Teacher-record bestaat dat aan deze 'user' gekoppeld is. Bestaat
    geen van beide, dan geeft de functie None terug (gebruiker zonder rol).
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

    Hoe het werkt: zoekt alle docenten die aan deze klas gekoppeld zijn.
    Als 'user' is meegegeven, wordt die docent zelf uitgesloten van de
    check (zodat een docent zijn eigen klas mag behouden/bewerken).
    Is er nog een ándere docent aan deze klas gekoppeld, dan wordt een
    ValidationError opgegooid met een duidelijke foutmelding.
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


def save_profile_for_role(*, role, user, name, class_group, existing_instance=None):
    """
    Slaat het profiel op in Student of Teacher volgens de gekozen rol,
    en verwijdert het profiel van de andere rol (een account is óf
    leerling óf docent, niet beide).

    Hoe het werkt, stap voor stap:
    1. Bepaal of de gewenste rol 'student' is (want_student).
    2. Is er al een bestaand profiel (existing_instance, bv. bij het
       bewerken van een account)?
       - Blijft de rol gelijk (Student->student of Teacher->teacher):
         update de gegevens en verwijder een eventueel profiel van de
         andere rol (opruimen).
       - Verandert de rol (bv. van Student naar Teacher): verwijder het
         oude profiel en maak/update een profiel van de nieuwe rol via
         update_or_create (maakt aan als het nog niet bestaat, anders
         wordt het bijgewerkt).
    3. Is er nog geen bestaand profiel (nieuw account): verwijder voor
       de zekerheid een eventueel profiel van de andere rol en maak
       daarna het juiste profiel aan/bij via update_or_create.
    Bij docenten wordt vóór het opslaan altijd gecontroleerd dat de
    gekozen klas nog geen andere docent heeft.
    """
    want_student = role == ROLE_STUDENT

    if existing_instance is not None:
        if isinstance(existing_instance, Student) and want_student:
            existing_instance.user = user
            existing_instance.name = name
            existing_instance.class_group = class_group
            existing_instance.save()
            Teacher.objects.filter(user=user).delete()
            return existing_instance

        if isinstance(existing_instance, Teacher) and not want_student:
            if class_group:
                _validate_teacher_class_group(class_group, user=user)
            existing_instance.user = user
            existing_instance.name = name
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
                defaults={'name': name, 'class_group': class_group or old_class_group},
            )
            return teacher

        if isinstance(existing_instance, Teacher) and want_student:
            existing_instance.delete()
            student, _ = Student.objects.update_or_create(
                user=user,
                defaults={'name': name, 'class_group': class_group or old_class_group},
            )
            return student

    if want_student:
        Teacher.objects.filter(user=user).delete()
        student, _ = Student.objects.update_or_create(
            user=user,
            defaults={'name': name, 'class_group': class_group},
        )
        return student

    if class_group:
        _validate_teacher_class_group(class_group, user=user)
    Student.objects.filter(user=user).delete()
    teacher, _ = Teacher.objects.update_or_create(
        user=user,
        defaults={'name': name, 'class_group': class_group},
    )
    return teacher
