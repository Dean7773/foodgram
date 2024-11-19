# Generated by Django 3.2.16 on 2024-11-19 16:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodgram', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='uniq_code',
            field=models.CharField(blank=True, max_length=4, unique=True),
        ),
        migrations.AlterField(
            model_name='ingredient',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
