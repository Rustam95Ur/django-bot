# Generated by Django 4.2.6 on 2023-12-16 10:07

import common_users.managers
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("common_users", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="commonuser",
            managers=[
                ("objects", common_users.managers.UserManager()),
            ],
        ),
    ]
