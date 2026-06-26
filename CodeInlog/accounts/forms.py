from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import ClassGroup, Student, Teacher
from .role_utils import (
    ROLE_CHOICES,
    ROLE_STUDENT,
    ROLE_TEACHER,
    save_profile_for_role,
    _validate_teacher_class_group,
)


class UserAccountFormMixin(forms.ModelForm):
    show_role = True
    default_role = ROLE_STUDENT

    email = forms.EmailField(label='E-mail', required=True)
    password = forms.CharField(
        label='Wachtwoord',
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'role' in self.fields:
            if self.instance.pk:
                if isinstance(self.instance, Student):
                    self.fields['role'].initial = ROLE_STUDENT
                elif isinstance(self.instance, Teacher):
                    self.fields['role'].initial = ROLE_TEACHER
            else:
                self.fields['role'].initial = self.default_role

        if self.instance.pk and getattr(self.instance, 'user_id', None):
            self.fields['email'].initial = self.instance.user.email
            self.fields['password'].help_text = 'Laat leeg om het wachtwoord niet te wijzigen.'
        else:
            self.fields['password'].required = True

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(username=email)
        if self.instance.pk and getattr(self.instance, 'user_id', None):
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError('Er bestaat al een account met dit e-mailadres.')
        return email

    def clean(self):
        cleaned = super().clean()
        if not self.show_role:
            return cleaned

        role = cleaned.get('role')
        class_group = cleaned.get('class_group')
        if role == ROLE_TEACHER and class_group:
            user = getattr(self.instance, 'user', None)
            try:
                _validate_teacher_class_group(class_group, user=user)
            except ValidationError as exc:
                for field, messages in exc.message_dict.items():
                    for message in messages:
                        self.add_error(field, message)

        if not self.instance.pk and not cleaned.get('password'):
            self.add_error('password', 'Wachtwoord is verplicht bij een nieuw account.')
        return cleaned

    def _ensure_user(self, instance, email, password):
        if instance.user_id:
            user = instance.user
            user.username = email
            user.email = email
            user.first_name = instance.first_name
            user.last_name = instance.last_name
            if password:
                user.set_password(password)
            user.save()
            return user

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=instance.first_name,
            last_name=instance.last_name,
        )
        instance.user = user
        return user

    def save(self, commit=True):
        email = self.cleaned_data['email']
        password = self.cleaned_data.get('password') or None
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']
        class_group = self.cleaned_data.get('class_group')
        role = self.cleaned_data.get('role', self.default_role)

        if not self.show_role:
            instance = super().save(commit=False)
            instance.first_name = first_name
            instance.last_name = last_name
            if commit:
                self._ensure_user(instance, email, password)
                instance.save()
                self.save_m2m()
            return instance

        if not commit:
            instance = super().save(commit=False)
            instance.first_name = first_name
            instance.last_name = last_name
            instance.class_group = class_group
            return instance

        if self.instance.pk:
            self.instance.first_name = first_name
            self.instance.last_name = last_name
            user = self._ensure_user(self.instance, email, password)
            return save_profile_for_role(
                role=role,
                user=user,
                first_name=first_name,
                last_name=last_name,
                class_group=class_group,
                existing_instance=self.instance,
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password or '',
            first_name=first_name,
            last_name=last_name,
        )
        return save_profile_for_role(
            role=role,
            user=user,
            first_name=first_name,
            last_name=last_name,
            class_group=class_group,
        )


class StudentAdminForm(UserAccountFormMixin):
    default_role = ROLE_STUDENT
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Rol', required=True)

    class Meta:
        model = Student
        fields = ('first_name', 'last_name', 'class_group', 'email', 'password', 'role')


class TeacherAdminForm(UserAccountFormMixin):
    default_role = ROLE_TEACHER
    role = forms.ChoiceField(choices=ROLE_CHOICES, label='Rol', required=True)

    class Meta:
        model = Teacher
        fields = ('first_name', 'last_name', 'class_group', 'email', 'password', 'role')


class StudentInlineForm(UserAccountFormMixin):
    show_role = False

    class Meta:
        model = Student
        fields = ('first_name', 'last_name', 'email', 'password')


class TeacherInlineForm(UserAccountFormMixin):
    show_role = False

    class Meta:
        model = Teacher
        fields = ('first_name', 'last_name', 'email', 'password')


class TeacherAddStudentForm(forms.Form):
    first_name = forms.CharField(label='Voornaam', max_length=150)
    last_name = forms.CharField(label='Achternaam', max_length=150)
    email = forms.EmailField(label='E-mail')
    password = forms.CharField(
        label='Wachtwoord',
        widget=forms.PasswordInput(render_value=False),
    )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(username=email).exists():
            raise forms.ValidationError('Er bestaat al een account met dit e-mailadres.')
        return email

    @property
    def full_name(self):
        return f'{self.cleaned_data["first_name"]} {self.cleaned_data["last_name"]}'.strip()

    def save(self, class_group):
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        first_name = self.cleaned_data['first_name']
        last_name = self.cleaned_data['last_name']

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        return Student.objects.create(
            user=user,
            first_name=first_name,
            last_name=last_name,
            class_group=class_group,
        )


class TeacherCreateStudentForm(TeacherAddStudentForm):
    class_group = forms.ModelChoiceField(
        queryset=ClassGroup.objects.order_by('name'),
        label='Klas',
    )

    def save(self):
        return super().save(class_group=self.cleaned_data['class_group'])
