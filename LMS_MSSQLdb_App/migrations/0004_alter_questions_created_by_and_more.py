# Generated by Django 4.1.13 on 2025-03-25 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS_MSSQLdb_App', '0003_students_info_allocate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questions',
            name='created_by',
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name='questions',
            name='last_updated_by',
            field=models.CharField(max_length=100),
        ),
    ]
