from django.contrib import admin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import StudentAdminForm, TeacherAdminForm, StudentInlineForm, TeacherInlineForm
from .models import ClassGroup, Student, Teacher
from .role_utils import ROLE_STUDENT, ROLE_TEACHER


# Admin-actie om geselecteerde studenten of docenten uit hun klas te verwijderen.
@admin.action(description='Uit klas verwijderen')
def remove_from_class(modeladmin, request, queryset):
    queryset.update(class_group=None)


# Inline-weergave van studenten binnen een klasgroep.
class StudentInline(admin.TabularInline):
    model = Student
    form = StudentInlineForm
    extra = 0
    can_delete = True
    verbose_name_plural = 'Studenten in deze klas'


# Inline-weergave van docenten binnen een klasgroep.
class TeacherInline(admin.TabularInline):
    model = Teacher
    form = TeacherInlineForm
    extra = 0
    can_delete = True
    verbose_name_plural = 'Docenten in deze klas'


# Admin-configuratie voor klasgroepen.
# Hiermee kunnen studenten en docenten direct binnen een klas worden beheerd.
class ClassGroupAdmin(admin.ModelAdmin):
    inlines = [StudentInline, TeacherInline]

    # Zorgt ervoor dat studenten en docenten correct aan een klas worden gekoppeld
    # of uit een klas worden verwijderd wanneer het formulier wordt opgeslagen.
    def save_formset(self, request, form, formset, change):
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


# Mixin die na een rolwissel automatisch naar het juiste admin-scherm doorstuurt.
class RoleSwitchAdminMixin:
    """Redirect naar de juiste admin-lijst na een rolwissel."""

    # Slaat het formulier op en onthoudt of het resultaat een student of docent is.
    def save_model(self, request, obj, form, change):
        saved = form.save()
        if isinstance(saved, Student):
            request._role_switch = ('student', saved.pk)
        elif isinstance(saved, Teacher):
            request._role_switch = ('teacher', saved.pk)

    # Bepaalt naar welk admin-scherm moet worden doorgestuurd.
    def _role_switch_redirect(self, request):
        info = getattr(request, '_role_switch', None)
        if not info:
            return None
        kind, pk = info
        if kind == 'student':
            return reverse('admin:accounts_student_change', args=[pk])
        return reverse('admin:accounts_teacher_change', args=[pk])

    # Wordt uitgevoerd nadat een bestaand object is gewijzigd.
    def response_change(self, request, obj):
        url = self._role_switch_redirect(request)
        if url:
            kind, _ = request._role_switch
            label = 'leerling' if kind == ROLE_STUDENT else 'docent'
            self.message_user(request, f'Account opgeslagen als {label}.')
            return HttpResponseRedirect(url)
        return super().response_change(request, obj)

    # Wordt uitgevoerd nadat een nieuw object is aangemaakt.
    def response_add(self, request, obj, post_url_continue=None):
        url = self._role_switch_redirect(request)
        if url:
            kind, _ = request._role_switch
            label = 'leerling' if kind == ROLE_STUDENT else 'docent'
            self.message_user(request, f'Account aangemaakt als {label}.')
            return HttpResponseRedirect(url)
        return super().response_add(request, obj, post_url_continue)


# Admin-scherm voor studenten.
@admin.register(Student)
class StudentAdmin(RoleSwitchAdminMixin, admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ('name', 'email', 'role_display', 'class_group')
    list_filter = ('class_group',)
    actions = [remove_from_class]

    # Toont het e-mailadres van de gekoppelde gebruiker.
    @admin.display(description='E-mail')
    def email(self, obj):
        return obj.user.email if obj.user_id else '—'

    # Toont de rol in de admin-lijst.
    @admin.display(description='Rol')
    def role_display(self, obj):
        return 'Leerling'


# Admin-scherm voor docenten.
@admin.register(Teacher)
class TeacherAdmin(RoleSwitchAdminMixin, admin.ModelAdmin):
    form = TeacherAdminForm
    list_display = ('name', 'email', 'role_display', 'class_group')
    list_filter = ('class_group',)
    actions = [remove_from_class]

    # Toont het e-mailadres van de gekoppelde gebruiker.
    @admin.display(description='E-mail')
    def email(self, obj):
        return obj.user.email if obj.user_id else '—'

    # Toont de rol in de admin-lijst.
    @admin.display(description='Rol')
    def role_display(self, obj):
        return 'Docent'


# Registreert de ClassGroup-admin.
admin.site.register(ClassGroup, ClassGroupAdmin)


# Aangepaste admin voor Django-groepen.
class GroupAdmin(admin.ModelAdmin):

    # Toont alle gebruikers die lid zijn van de groep.
    def users(self, obj):
        return ", ".join([user.username for user in obj.user_set.all()])

    list_display = ('name', 'users')


# Vervangt de standaard Django Group-admin door de aangepaste versie.
admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)