# Generated by Django 5.1.4 on 2024-12-06 12:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("main_app", "0009_alter_shuttleinstance_common_prefix"),
    ]

    operations = [
        migrations.RenameField(
            model_name="shuttleinstance",
            old_name="common_prefix",
            new_name="common_name_parts",
        ),
    ]
