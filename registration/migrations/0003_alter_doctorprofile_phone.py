# Generated by Django 5.1.4 on 2024-12-13 16:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_remove_user_phone_doctorprofile_phone_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='doctorprofile',
            name='phone',
            field=models.CharField(max_length=15),
        ),
    ]
