# Generated by Django 4.2.15 on 2024-09-28 09:25

from django.db import migrations, models
import django.utils.timezone
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('users', '0002_remove_customuser_description_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscribedUsers',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=100, unique=True)),
                ('created_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='Date created')),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='description',
            field=models.TextField(blank=True, default='', max_length=600, verbose_name='Description'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='image',
            field=models.ImageField(default='default/user.jpg', upload_to=users.models.CustomUser.image_upload_to),
        ),
        migrations.AddField(
            model_name='customuser',
            name='status',
            field=models.CharField(choices=[('regular', 'regular'), ('subscriber', 'subscriber'), ('moderator', 'moderator')], default='regular', max_length=100),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups'),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions'),
        ),
    ]
