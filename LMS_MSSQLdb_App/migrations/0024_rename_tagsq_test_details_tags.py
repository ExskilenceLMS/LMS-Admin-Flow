# Generated by Django 4.1.13 on 2025-04-22 04:23

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('LMS_MSSQLdb_App', '0023_remove_test_details_tags_test_details_tagsq'),
    ]

    operations = [
        migrations.RenameField(
            model_name='test_details',
            old_name='tagsq',
            new_name='tags',
        ),
    ]
