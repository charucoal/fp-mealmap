# Generated by Django 4.2.16 on 2025-02-24 15:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("webdata", "0015_alter_dietaryreg_business"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="fooditem",
            name="business",
        ),
        migrations.DeleteModel(
            name="Alert",
        ),
        migrations.DeleteModel(
            name="Business",
        ),
        migrations.DeleteModel(
            name="Customer",
        ),
        migrations.DeleteModel(
            name="FoodItem",
        ),
    ]
