from django.conf import settings
from django.db import models


class ClassGroup(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


class PersonProfileMixin(models.Model):
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
