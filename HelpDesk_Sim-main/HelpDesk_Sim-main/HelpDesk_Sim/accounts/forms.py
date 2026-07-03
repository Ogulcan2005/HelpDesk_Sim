from django import forms
from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Student, Teacher
from .role_utils import (
    ROLE_CHOICES,
    ROLE_STUDENT,
    ROLE_TEACHER,
    save_profile_for_role,
    _validate_teacher_class_group,
)


# =============================================================================
# Formulieren voor "wachtwoord vergeten"
# =============================================================================


class DutchPasswordResetForm(PasswordResetForm):
    """
    Stap 1: e-mail invullen om een resetlink te ontvangen.

    Erft van Django's PasswordResetForm. Alleen labels en placeholder
    worden in het Nederlands gezet voor de pagina /reset_password/.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['email'].label = 'E-mailadres'
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Vul je e-mailadres in',
        })


class DutchSetPasswordForm(SetPasswordForm):
    """
    Stap 3: nieuw wachtwoord kiezen via de link uit de e-mail.

    Erft van Django's SetPasswordForm. De gebruiker vult het wachtwoord
    twee keer in; Django checkt of ze gelijk zijn en voldoen aan
    AUTH_PASSWORD_VALIDATORS in settings.py.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['new_password1'].label = 'Nieuw wachtwoord'
        self.fields['new_password2'].label = 'Bevestig nieuw wachtwoord'

        for field_name in ('new_password1', 'new_password2'):
            self.fields[field_name].widget.attrs.update({
                'placeholder': self.fields[field_name].label,
            })


# =============================================================================
# Formulieren voor accountbeheer (admin / registratie)
# =============================================================================


class UserAccountFormMixin(forms.ModelForm):
    """
    Gedeelde basis voor alle account-formulieren (Student/Teacher,
    los formulier of inline-formulier in de admin).

    Hoe het werkt: dit ModelForm voegt drie extra velden toe die niet
    rechtstreeks op het Student/Teacher-model staan, maar wel nodig zijn
    om een Django 'User'-login-account te beheren: email, password en role.
    Subclasses bepalen via 'show_role' of het rolveld getoond wordt, en
    via 'default_role' welke rol standaard gekozen is voor nieuwe accounts.
    """
    show_role = True
    default_role = ROLE_STUDENT

    email = forms.EmailField(label='E-mail', required=True)
    password = forms.CharField(
        label='Wachtwoord',
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label='Rol',
        required=True,
    )

    def __init__(self, *args, **kwargs):
        """
        Stelt de begintoestand van het formulier in.

        Hoe het werkt: als 'show_role' False is (inline-formulieren),
        wordt het rolveld helemaal verwijderd. Anders wordt de juiste
        rol vooraf ingevuld: bij een bestaand Student/Teacher-object op
        basis van het type van dat object, en bij een nieuw object op
        basis van 'default_role'. Bij een bestaand account met een
        gekoppelde 'user' wordt ook het e-mailveld voorgevuld en krijgt
        het wachtwoordveld een hint dat het optioneel is bij bewerken
        (leeg laten = wachtwoord niet wijzigen). Bij een nieuw account
        is het wachtwoord wél verplicht.
        """
        super().__init__(*args, **kwargs)
        if not self.show_role:
            self.fields.pop('role', None)
        elif self.instance.pk:
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
        """
        Validatie van het e-mailveld: voorkomt dubbele accounts.

        Hoe het werkt: het e-mailadres wordt genormaliseerd (kleine
        letters, geen spaties) en er wordt gecontroleerd of er al een
        User met dit e-mailadres als username bestaat. Bij het bewerken
        van een bestaand account wordt dat account zelf uitgesloten van
        de check (anders zou je je eigen e-mailadres niet kunnen
        'hergebruiken').
        """
        email = self.cleaned_data['email'].strip().lower()
        qs = User.objects.filter(username=email)
        if self.instance.pk and getattr(self.instance, 'user_id', None):
            qs = qs.exclude(pk=self.instance.user_id)
        if qs.exists():
            raise forms.ValidationError('Er bestaat al een account met dit e-mailadres.')
        return email

    def clean(self):
        """
        Validatie die meerdere velden samen controleert.

        Hoe het werkt: als de rol 'docent' is en er een klas gekozen
        is, wordt gecontroleerd dat die klas nog geen andere docent
        heeft (_validate_teacher_class_group). Eventuele fouten daaruit
        worden toegevoegd aan het formulier zodat ze bij het juiste veld
        getoond worden. Daarnaast wordt bij een nieuw account afgedwongen
        dat er een wachtwoord is ingevuld.
        """
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
        """
        Maakt een Django 'User' aan, of werkt een bestaande bij.

        Hoe het werkt: heeft het Student/Teacher-profiel al een
        gekoppelde user, dan worden username/email/naam bijgewerkt, en
        wordt het wachtwoord alleen aangepast als er een nieuw
        wachtwoord is ingevuld (set_password). Bestaat er nog geen user,
        dan wordt er een nieuwe aangemaakt en aan het profiel gekoppeld
        (instance.user = user), zodat save() hierna het profiel kan
        opslaan met de juiste koppeling.
        """
        if instance.user_id:
            user = instance.user
            user.username = email
            user.email = email
            user.first_name = instance.name
            if password:
                user.set_password(password)
            user.save()
            return user

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=instance.name,
        )
        instance.user = user
        return user

    def save(self, commit=True):
        """
        Slaat het formulier op: zowel het login-account (User) als het
        Student- of Teacher-profiel, afhankelijk van de gekozen rol.

        Hoe het werkt, per situatie:
        - show_role is False (inline-formulier zonder rolkeuze): sla het
          profiel op zoals een gewoon ModelForm, en zorg via _ensure_user
          dat er een passend User-account bij hoort.
        - commit is False: er wordt nog niets definitief opgeslagen
          (bijvoorbeeld omdat de admin dat later zelf doet), enkel het
          in-memory object wordt klaargezet.
        - Bestaand profiel (self.instance.pk): werk eerst de User bij,
          en laat save_profile_for_role() bepalen of het profiel
          Student of Teacher moet zijn/blijven (rolwissel mogelijk).
        - Nieuw profiel: maak eerst een User aan en laat daarna
          save_profile_for_role() het juiste profiel aanmaken.
        """
        email = self.cleaned_data['email']
        password = self.cleaned_data.get('password') or None
        name = self.cleaned_data['name']
        class_group = self.cleaned_data.get('class_group')
        role = self.cleaned_data.get('role', self.default_role)

        if not self.show_role:
            instance = super().save(commit=False)
            instance.name = name
            if commit:
                self._ensure_user(instance, email, password)
                instance.save()
                self.save_m2m()
            return instance

        if not commit:
            instance = super().save(commit=False)
            instance.name = name
            instance.class_group = class_group
            return instance

        if self.instance.pk:
            self.instance.name = name
            user = self._ensure_user(self.instance, email, password)
            return save_profile_for_role(
                role=role,
                user=user,
                name=name,
                class_group=class_group,
                existing_instance=self.instance,
            )

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password or '',
            first_name=name,
        )
        return save_profile_for_role(
            role=role,
            user=user,
            name=name,
            class_group=class_group,
        )


class StudentAdminForm(UserAccountFormMixin):
    """Formulier voor het aanmaken/bewerken van een leerling in de admin, mét rolkeuze."""
    default_role = ROLE_STUDENT

    class Meta:
        model = Student
        fields = ('name', 'class_group', 'email', 'password', 'role')


class TeacherAdminForm(UserAccountFormMixin):
    """Formulier voor het aanmaken/bewerken van een docent in de admin, mét rolkeuze."""
    default_role = ROLE_TEACHER

    class Meta:
        model = Teacher
        fields = ('name', 'class_group', 'email', 'password', 'role')


class StudentInlineForm(UserAccountFormMixin):
    """Compact formulier voor leerlingen, gebruikt als inline-rij binnen een klas (geen rolkeuze nodig)."""
    show_role = False

    class Meta:
        model = Student
        fields = ('name', 'email', 'password')


class TeacherInlineForm(UserAccountFormMixin):
    """Compact formulier voor docenten, gebruikt als inline-rij binnen een klas (geen rolkeuze nodig)."""
    show_role = False

    class Meta:
        model = Teacher
        fields = ('name', 'email', 'password')
