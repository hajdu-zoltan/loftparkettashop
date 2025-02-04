# Generated by Django 4.2.15 on 2025-02-04 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0026_alter_order_barion_id_alter_order_barion_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='news',
            name='content',
            field=models.TextField(blank=True, null=True, verbose_name='Termék'),
        ),
        migrations.AlterField(
            model_name='news',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Létrehozva'),
        ),
        migrations.AlterField(
            model_name='news',
            name='title',
            field=models.CharField(max_length=200, verbose_name='Cím'),
        ),
        migrations.AlterField(
            model_name='news',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Frissítve'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='quantity',
            field=models.IntegerField(verbose_name='Mennyiség'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='total_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Teljes ár'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Egység ár'),
        ),
    ]
