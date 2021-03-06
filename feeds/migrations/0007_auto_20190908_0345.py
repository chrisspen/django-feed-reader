# Generated by Django 2.2.4 on 2019-09-08 03:45

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0006_auto_20190901_1827'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='due_poll',
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0)),
        ),
        migrations.AlterField(
            model_name='source',
            name='last_change',
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0), null=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='last_success',
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0), null=True),
        ),
    ]
