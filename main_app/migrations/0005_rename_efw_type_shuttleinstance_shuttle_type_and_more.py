# Generated by Django 5.0.6 on 2024-05-16 07:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0004_shuttleinstance'),
    ]

    operations = [
        migrations.RenameField(
            model_name='shuttleinstance',
            old_name='efw_type',
            new_name='shuttle_type',
        ),
        migrations.AlterField(
            model_name='shuttleinstance',
            name='name',
            field=models.CharField(help_text='Unique name of the Shuttle instance. This name cannot be changed!', max_length=50, unique=True),
        ),
    ]
