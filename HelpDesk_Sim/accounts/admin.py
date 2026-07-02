from django.contrib import admin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import StudentAdminForm, TeacherAdminForm, StudentInlineForm, TeacherInlineForm
from .models import ClassGroup, Student, Teacher
from .role_utils import ROLE_STUDENT, ROLE_TEACHER


@admin.action(description='Uit klas verwijderen')
def remove_from_class(modeladmin, request, queryset):
    """
    Admin-actie (bulkactie) die geselecteerde leerlingen/docenten loskoppelt
    van hun klas, zonder de accounts zelf te verwijderen.

    Hoe het werkt: 'queryset.update(class_group=None)' zet in één
    databasequery het klas-veld van alle geselecteerde rijen op None.
    """
    queryset.update(class_group=None)


class StudentInline(admin.TabularInline):
    """
    Laat leerlingen zien/bewerken als tabel-rijen binnen de admin-pagina
    van een ClassGroup (in plaats van een apart scherm).
    """
    model = Student
    form = StudentInlineForm
    fields = ('name', 'email', 'password')
    extra = 0
    can_delete = True
    verbose_name_plural = 'Studenten in deze klas'


class TeacherInline(admin.TabularInline):
    """
    Laat docenten zien/bewerken als tabel-rijen binnen de admin-pagina
    van een ClassGroup (in plaats van een apart scherm).
    """
    model = Teacher
    form = TeacherInlineForm
    fields = ('name', 'email', 'password')
    extra = 0
    can_delete = True
    verbose_name_plural = 'Docenten in deze klas'


class ClassGroupAdmin(admin.ModelAdmin):
    """
    Admin-configuratie voor ClassGroup: toont de Student- en
    Teacher-inlines direct op de klas-pagina.
    """
    inlines = [StudentInline, TeacherInline]

    def save_formset(self, request, form, formset, change):
        """
        Verwerkt het opslaan van de inline-tabellen (studenten/docenten)
        op de klas-pagina.

        Hoe het werkt: voor het Student/Teacher-formset wordt elke rij
        eerst voorbereid zonder op te slaan (commit=False), waarna de
        klas (form.instance, dus de ClassGroup die je aan het bewerken
        bent) er handmatig aan toegekend wordt vóór het echte save().
        Verwijderde rijen (formset.deleted_objects) worden niet
        weggegooid, maar krijgen class_group=None: ze blijven bestaan
        als los account, maar horen niet meer bij deze klas.
        Voor andere formsets (niet Student/Teacher) wordt gewoon het
        standaardgedrag van Django gebruikt.
        """
        if formset.model not in (Student, Teacher):
            super().save_formset(request, form, formset, change)
            return

        instances = formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.class_group = None
            obj.save(update_fields=['class_group'])
        for instance in instances:
            instance.class_group = form.instance
            instance.save()
        formset.save_m2m()


class RoleSwitchAdminMixin:
    """Redirect naar de juiste admin-lijst na een rolwissel."""

    def save_model(self, request, obj, form, change):
        """
        Wordt aangeroepen door Django wanneer een Student/Teacher-object
        via de admin wordt opgeslagen.

        Hoe het werkt: in plaats van het standaard obj.save() te
        gebruiken, wordt form.save() aangeroepen (zie forms.py), omdat
        dat formulier ook de rolwissel-logica afhandelt en mogelijk een
        ander type object teruggeeft (bv. Student wordt Teacher). Het
        resultaat wordt tijdelijk op het request gezet, zodat
        response_add/response_change hierna weten waar ze naar moeten
        doorverwijzen.
        """
        saved = form.save()
        if isinstance(saved, Student):
            request._role_switch = ('student', saved.pk)
        elif isinstance(saved, Teacher):
            request._role_switch = ('teacher', saved.pk)

    def _role_switch_redirect(self, request):
        """
        Bepaalt, op basis van wat save_model() heeft opgeslagen op het
        request, naar welke admin-pagina doorgestuurd moet worden.
        Geeft None terug als er geen rolwissel heeft plaatsgevonden.
        """
        info = getattr(request, '_role_switch', None)
        if not info:
            return None
        kind, pk = info
        if kind == 'student':
            return reverse('admin:accounts_student_change', args=[pk])
        return reverse('admin:accounts_teacher_change', args=[pk])

    def response_change(self, request, obj):
        """
        Overschrijft het standaard 'na opslaan'-gedrag bij het bewerken
        van een bestaand object: is er een rolwissel geweest (bv. van
        leerling naar docent), dan wordt er doorgestuurd naar de
        admin-pagina van het nieuwe type, met een duidelijk bericht.
        Anders gebeurt gewoon het standaardgedrag van Django.
        """
        url = self._role_switch_redirect(request)
        if url:
            kind, _ = request._role_switch
            label = 'leerling' if kind == ROLE_STUDENT else 'docent'
            self.message_user(request, f'Account opgeslagen als {label}.')
            return HttpResponseRedirect(url)
        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Zelfde idee als response_change(), maar dan voor het aanmaken
        van een nieuw account: stuurt na het opslaan door naar de
        juiste admin-pagina (leerling of docent) met een bevestiging.
        """
        url = self._role_switch_redirect(request)
        if url:
            kind, _ = request._role_switch
            label = 'leerling' if kind == ROLE_STUDENT else 'docent'
            self.message_user(request, f'Account aangemaakt als {label}.')
            return HttpResponseRedirect(url)
        return super().response_add(request, obj, post_url_continue)


@admin.register(Student)
class StudentAdmin(RoleSwitchAdminMixin, admin.ModelAdmin):
    """Admin-configuratie voor het beheren van leerlingen."""
    form = StudentAdminForm
    list_display = ('name', 'email', 'role_display', 'class_group')
    list_filter = ('class_group',)
    actions = [remove_from_class]

    @admin.display(description='E-mail')
    def email(self, obj):
        # Kolom in de lijstweergave: toont het e-mailadres van de
        # gekoppelde User, of een streepje als er nog geen account is.
        return obj.user.email if obj.user_id else '—'

    @admin.display(description='Rol')
    def role_display(self, obj):
        # Kolom in de lijstweergave: voor deze admin altijd 'Leerling'.
        return 'Leerling'


@admin.register(Teacher)
class TeacherAdmin(RoleSwitchAdminMixin, admin.ModelAdmin):
    """Admin-configuratie voor het beheren van docenten."""
    form = TeacherAdminForm
    list_display = ('name', 'email', 'role_display', 'class_group')
    list_filter = ('class_group',)
    actions = [remove_from_class]

    @admin.display(description='E-mail')
    def email(self, obj):
        # Kolom in de lijstweergave: toont het e-mailadres van de
        # gekoppelde User, of een streepje als er nog geen account is.
        return obj.user.email if obj.user_id else '—'

    @admin.display(description='Rol')
    def role_display(self, obj):
        # Kolom in de lijstweergave: voor deze admin altijd 'Docent'.
        return 'Docent'


admin.site.register(ClassGroup, ClassGroupAdmin)


class GroupAdmin(admin.ModelAdmin):
    """
    Aangepaste admin voor Django's ingebouwde 'Group'-model (rechten-
    groepen), met een extra kolom die laat zien welke gebruikers in de
    groep zitten.
    """
    def users(self, obj):
        # Kolom in de lijstweergave: komma-gescheiden lijst van
        # gebruikersnamen die tot deze groep behoren.
        return ", ".join([user.username for user in obj.user_set.all()])

    list_display = ('name', 'users')


# Vervangt Django's standaard Group-admin door de aangepaste versie hierboven.
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
