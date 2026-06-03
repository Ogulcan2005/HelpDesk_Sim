from django.contrib import admin
from django.contrib.auth.models import Group
from .models import ClassGroup, Student, Teacher


class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


class TeacherInline(admin.TabularInline):
    model = Teacher.class_groups.through
    extra = 0


class ClassGroupAdmin(admin.ModelAdmin):
    inlines = [StudentInline, TeacherInline]


admin.site.register(ClassGroup, ClassGroupAdmin)
admin.site.register(Student)
admin.site.register(Teacher)


class GroupAdmin(admin.ModelAdmin):
    def users(self, obj):
        return ", ".join([user.username for user in obj.user_set.all()])

    list_display = ('name', 'users')


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)