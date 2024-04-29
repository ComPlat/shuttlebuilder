# Generated by Django 4.0.4 on 2022-08-31 05:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Dashboard', '0004_remove_instance_type_instance_efw_type_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='instance',
            name='efw_type',
            field=models.CharField(choices=[('file', 'File'), ('folder', 'Folder'), ('zip', 'ZIP')], help_text="Type must be 'file', 'folder' or 'zip'. The 'file' option means that each file is handled individually, the 'folder' option means that entire folders are transmitted only when all files in them are ready. The option 'zip' sends a folder zipped, only when all files in a folder are ready.", max_length=255, verbose_name='Type'),
        ),
    ]
