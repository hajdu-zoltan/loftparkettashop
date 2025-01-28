# Generated by Django 4.2.15 on 2025-01-28 19:55

import ckeditor.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0018_alter_product_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='description',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='popularity',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='product',
            name='sort_description',
            field=ckeditor.fields.RichTextField(blank=True, null=True),
        ),
    ]
