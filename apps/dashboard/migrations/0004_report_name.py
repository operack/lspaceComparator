# Generated by Django 5.1.6 on 2025-03-31 16:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_item_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='report',
            name='name',
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
