# Generated by Django 5.1.4 on 2024-12-06 12:25

from django.db import migrations

def migrate_time_to_positive_int(apps, schema_editor):

    MyModel = apps.get_model('main_app', 'ShuttleInstance')

    for mm in MyModel.objects.all():
        try:
            field_old_time = int(mm.common_name_parts)
            mm.common_name_parts = f"^.{{{field_old_time}}}"
            mm.save()
        except:
            pass



class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0011_alter_shuttleinstance_common_name_parts"),
    ]

    operations = [
        migrations.RunPython(migrate_time_to_positive_int)
    ]