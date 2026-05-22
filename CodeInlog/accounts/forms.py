from django import forms
from django.contrib.auth.models import User


class UserAccountFormMixin(forms.ModelForm):
    email = forms.EmailField(label='E-mail', required=True)
    password = forms.CharField(
        label='Wachtwoord',
        widget=forms.PasswordInput(render_value=False),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        if not self.instance.pk and not cleaned.get('password'):
            self.add_error('password', 'Wachtwoord is verplicht bij een nieuw account.')
        return cleaned

    def _sync_user(self, instance, email, password):
        if instance.user_id:
            user = instance.user
            user.username = email
            user.email = email
            user.first_name = instance.name
            if password:
                user.set_password(password)
            user.save()
        else:
            instance.user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=instance.name,
            )

    def save(self, commit=True):
        instance = super().save(commit=False)
        email = self.cleaned_data['email']
        password = self.cleaned_data.get('password') or None
        self._sync_user(instance, email, password)
        if commit:
            instance.save()
            self.save_m2m()
        return instance
