# Generated by Django 4.2.16 on 2025-01-31 07:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("webdata", "0002_remove_customuser_account_type2"),
    ]

    operations = [
        migrations.DeleteModel(
            name="newtable",
        ),
        migrations.AlterField(
            model_name="customerinfo",
            name="lat",
            field=models.FloatField(),
        ),
        migrations.AlterField(
            model_name="customerinfo",
            name="long",
            field=models.FloatField(),
        ),
    ]
