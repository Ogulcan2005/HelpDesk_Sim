from django.core.exceptions import ValidationError

from .models import Student, Teacher

ROLE_STUDENT = 'student'
ROLE_TEACHER = 'teacher'

ROLE_CHOICES = [
    (ROLE_STUDENT, 'Leerling'),
    (ROLE_TEACHER, 'Docent'),
]


def profile_role_for_user(user):
    if user is None:
        return None
    if Student.objects.filter(user=user).exists():
        return ROLE_STUDENT
    if Teacher.objects.filter(user=user).exists():
        return ROLE_TEACHER
    return None


def _validate_teacher_class_group(class_group, user=None):
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
    """Slaat het profiel op in Student of Teacher volgens role. Verwijdert het andere profiel."""
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
