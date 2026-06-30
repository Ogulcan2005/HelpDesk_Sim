"""
Database-modellen voor accounts, klassen en rollen.

Structuur:
    ClassGroup   → een schoolklas (bijv. "3A")
    Student      → leerlingprofiel + koppeling aan login-account (User)
    Teacher      → docentprofiel + koppeling aan login-account (User)

Elke leerling/docent heeft een Django User voor inloggen. Het profiel
(Student of Teacher) bepaalt de rol. PersonProfileMixin voegt voornaam
en achternaam toe aan beide profieltypes.
"""
from django.conf import settings
from django.db import models


class ClassGroup(models.Model):
    """
    Een schoolklas/groep.

    Relaties:
    - Meerdere Student-records kunnen aan één klas hangen (ForeignKey).
    - Precies één Teacher kan aan één klas hangen (OneToOneField).
    """
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class PersonProfileMixin(models.Model):
    """
    Gedeelde velden voor Student en Teacher: voornaam en achternaam.

    full_name combineert beide velden tot één leesbare naam voor
    templates, admin-lijsten en succesmeldingen.
    """
    first_name = models.CharField(max_length=150, verbose_name='Voornaam')
    last_name = models.CharField(max_length=150, verbose_name='Achternaam')

    class Meta:
        abstract = True

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    def __str__(self):
        return self.full_name or '—'


class Student(PersonProfileMixin, models.Model):
    """
    Profiel van een leerling.

    user:       OneToOne naar Django User (voor inloggen met e-mail)
    class_group: optionele koppeling aan een klas (kan leeg zijn)
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_profile',
    )
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


class Teacher(PersonProfileMixin, models.Model):
    """
    Profiel van een docent.

    user:        OneToOne naar Django User (voor inloggen)
    class_group: OneToOne naar ClassGroup (max. één docent per klas)
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teacher_profile',
    )
    class_group = models.OneToOneField(
        ClassGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
