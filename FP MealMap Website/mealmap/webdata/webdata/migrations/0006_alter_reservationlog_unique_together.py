# Generated by Django 4.2.16 on 2025-02-01 11:08

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("webdata", "0005_remove_reservationlog_collected_and_more"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="reservationlog",
            unique_together={("item", "customer", "res_status")},
        ),
    ]
