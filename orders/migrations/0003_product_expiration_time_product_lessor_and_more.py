# Generated by Django 4.2.6 on 2023-12-17 23:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("orders", "0002_product_is_free"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="expiration_time",
            field=models.TimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="product",
            name="lessor",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Lessor",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="category",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="products",
                to="orders.category",
                verbose_name="Category",
            ),
        ),
    ]
