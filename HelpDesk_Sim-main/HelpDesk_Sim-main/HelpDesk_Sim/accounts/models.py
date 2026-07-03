from django.conf import settings
from django.db import models


class ClassGroup(models.Model):
    """
    Een schoolklas/groep. Eén klas kan meerdere studenten bevatten en
    (in dit ontwerp) precies één docent.
    """
    name = models.CharField(max_length=50)

    def __str__(self):
        # Laat de klasnaam zien in plaats van "ClassGroup object (1)"
        return self.name


class Student(models.Model):
    """
    Profiel van een leerling, gekoppeld aan een Django 'User'-account
    (voor inloggen) en optioneel aan een klas.

    Hoe het werkt: 'user' is een 1-op-1 koppeling met het login-account.
    Als een gebruiker geen Student-profiel heeft, is hij geen leerling.
    role_utils.py gebruikt het bestaan van dit profiel om de rol van
    een gebruiker te bepalen.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='student_profile',
    )
    name = models.CharField(max_length=100)
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        # Laat de naam van de leerling zien in lijsten/dropdowns
        return self.name


class Teacher(models.Model):
    """
    Profiel van een docent, gekoppeld aan een Django 'User'-account.

    Hoe het werkt: een docent kan precies één klas onder zich hebben
    (OneToOneField naar ClassGroup). role_utils.py controleert dat een
    klas niet aan twee docenten tegelijk gekoppeld wordt.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='teacher_profile',
    )
    name = models.CharField(max_length=100)
    class_group = models.OneToOneField(
        ClassGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        # Laat de naam van de docent zien in lijsten/dropdowns
        return self.name
