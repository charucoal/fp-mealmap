# Generated by Django 4.2.16 on 2025-02-24 15:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("webdata", "0014_dietaryreg_delete_dietaryneeds"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dietaryreg",
            name="business",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="dietary_preferences",
                to="webdata.businessinfo",
            ),
        ),
    ]
