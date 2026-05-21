from django.contrib import admin
from django.contrib.auth.models import Group
from .models import ClassGroup, Student, Teacher


@admin.action(description='Uit klas verwijderen')
def remove_from_class(modeladmin, request, queryset):
    queryset.update(class_group=None)


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0
    can_delete = True
    verbose_name_plural = 'Studenten in deze klas'


class TeacherInline(admin.TabularInline):
    model = Teacher
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


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_group')
    list_filter = ('class_group',)
    actions = [remove_from_class]


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('name', 'class_group')
    list_filter = ('class_group',)
    actions = [remove_from_class]


admin.site.register(ClassGroup, ClassGroupAdmin)


class GroupAdmin(admin.ModelAdmin):
    def users(self, obj):
        return ", ".join([user.username for user in obj.user_set.all()])

    list_display = ('name', 'users')


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)