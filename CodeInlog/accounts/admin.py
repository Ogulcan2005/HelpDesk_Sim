from django.contrib import admin
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import reverse

from .forms import StudentAdminForm, TeacherAdminForm, StudentInlineForm, TeacherInlineForm
from .models import ClassGroup, Student, Teacher
from .role_utils import ROLE_STUDENT, ROLE_TEACHER


@admin.action(description='Uit klas verwijderen')
def remove_from_class(modeladmin, request, queryset):
    queryset.update(class_group=None)


class StudentInline(admin.TabularInline):
    model = Student
    form = StudentInlineForm
    extra = 0
    can_delete = True
    verbose_name_plural = 'Studenten in deze klas'


class TeacherInline(admin.TabularInline):
    model = Teacher
    form = TeacherInlineForm
    extra = 0
    can_delete = True
    verbose_name_plural = 'Docenten in deze klas'


class ClassGroupAdmin(admin.ModelAdmin):
    inlines = [StudentInline, TeacherInline]

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


class RoleSwitchAdminMixin:
    """Redirect naar de juiste admin-lijst na een rolwissel."""

    def save_model(self, request, obj, form, change):
        saved = form.save()
        if isinstance(saved, Student):
            request._role_switch = ('student', saved.pk)
        elif isinstance(saved, Teacher):
            request._role_switch = ('teacher', saved.pk)

    def _role_switch_redirect(self, request):
        info = getattr(request, '_role_switch', None)
        if not info:
            return None
        kind, pk = info
        if kind == 'student':
            return reverse('admin:accounts_student_change', args=[pk])
        return reverse('admin:accounts_teacher_change', args=[pk])

    def response_change(self, request, obj):
        url = self._role_switch_redirect(request)
        if url:
            kind, _ = request._role_switch
            label = 'leerling' if kind == ROLE_STUDENT else 'docent'
            self.message_user(request, f'Account opgeslagen als {label}.')
            return HttpResponseRedirect(url)
        return super().response_change(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        url = self._role_switch_redirect(request)
        if url:
            kind, _ = request._role_switch
            label = 'leerling' if kind == ROLE_STUDENT else 'docent'
            self.message_user(request, f'Account aangemaakt als {label}.')
            return HttpResponseRedirect(url)
        return super().response_add(request, obj, post_url_continue)


@admin.register(Student)
class StudentAdmin(RoleSwitchAdminMixin, admin.ModelAdmin):
    form = StudentAdminForm
    list_display = ('name', 'email', 'role_display', 'class_group')
    list_filter = ('class_group',)
    actions = [remove_from_class]

    @admin.display(description='E-mail')
    def email(self, obj):
        return obj.user.email if obj.user_id else '—'

    @admin.display(description='Rol')
    def role_display(self, obj):
        return 'Leerling'


@admin.register(Teacher)
class TeacherAdmin(RoleSwitchAdminMixin, admin.ModelAdmin):
    form = TeacherAdminForm
    list_display = ('name', 'email', 'role_display', 'class_group')
    list_filter = ('class_group',)
    actions = [remove_from_class]

    @admin.display(description='E-mail')
    def email(self, obj):
        return obj.user.email if obj.user_id else '—'

    @admin.display(description='Rol')
    def role_display(self, obj):
        return 'Docent'


admin.site.register(ClassGroup, ClassGroupAdmin)


class GroupAdmin(admin.ModelAdmin):
    def users(self, obj):
        return ", ".join([user.username for user in obj.user_set.all()])

    list_display = ('name', 'users')


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
