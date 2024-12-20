# Generated by Django 4.2.15 on 2024-11-20 17:57

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('draw', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('unique_link', models.UUIDField(default=uuid.uuid4, unique=True)),
                ('has_drawn', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('drawn_family_name', models.CharField(max_length=100)),
                ('participant', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='draw.participant')),
            ],
        ),
        migrations.RenameField(
            model_name='familyname',
            old_name='is_drawn',
            new_name='drawn',
        ),
        migrations.AlterField(
            model_name='familyname',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.DeleteModel(
            name='DrawResult',
        ),
    ]
