from django.db import migrations, models


def split_name_fields(apps, schema_editor):
    for model_name in ('Student', 'Teacher'):
        Model = apps.get_model('accounts', model_name)
        for obj in Model.objects.all():
            parts = (obj.name or '').strip().split(None, 1)
            obj.first_name = parts[0] if parts else ''
            obj.last_name = parts[1] if len(parts) > 1 else ''
            obj.save(update_fields=['first_name', 'last_name'])

            if obj.user_id:
                user = obj.user
                user.first_name = obj.first_name
                user.last_name = obj.last_name
                user.save(update_fields=['first_name', 'last_name'])


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_student_teacher_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='first_name',
            field=models.CharField(default='', max_length=150, verbose_name='Voornaam'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='student',
            name='last_name',
            field=models.CharField(default='', max_length=150, verbose_name='Achternaam'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='teacher',
            name='first_name',
            field=models.CharField(default='', max_length=150, verbose_name='Voornaam'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='teacher',
            name='last_name',
            field=models.CharField(default='', max_length=150, verbose_name='Achternaam'),
            preserve_default=False,
        ),
        migrations.RunPython(split_name_fields, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='student',
            name='name',
        ),
        migrations.RemoveField(
            model_name='teacher',
            name='name',
        ),
    ]
