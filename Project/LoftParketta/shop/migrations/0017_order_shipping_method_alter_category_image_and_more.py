# Generated by Django 4.2.15 on 2025-01-18 12:42

from django.db import migrations, models
import versatileimagefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0016_alter_product_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='shipping_method',
            field=models.CharField(choices=[('store_pickup', 'Boltban történő átvétel'), ('home_delivery', 'Házhoz szállítás Szegeden'), ('free_shipping', 'Ingyenes szállítás Szegeden belül')], default='store_pickup', max_length=20),
        ),
        migrations.AlterField(
            model_name='category',
            name='image',
            field=versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='category_images/', verbose_name='Image'),
        ),
        migrations.AlterField(
            model_name='news',
            name='image',
            field=versatileimagefield.fields.VersatileImageField(blank=True, null=True, upload_to='news_images/', verbose_name='Image'),
        ),
    ]
