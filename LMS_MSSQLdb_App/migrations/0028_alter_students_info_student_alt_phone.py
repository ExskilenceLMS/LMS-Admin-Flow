# Generated by Django 4.1.13 on 2025-04-22 05:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LMS_MSSQLdb_App', '0027_rename_tags2_questions_tags'),
    ]

    operations = [
        migrations.AlterField(
            model_name='students_info',
            name='student_alt_phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
