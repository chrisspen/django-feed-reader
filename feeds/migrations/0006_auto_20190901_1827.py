# Generated by Django 2.2.4 on 2019-09-01 18:27

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0005_source_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='enclosure',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='enclosures', to='feeds.Post'),
        ),
        migrations.AlterField(
            model_name='post',
            name='source',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='feeds.Source'),
        ),
        migrations.AlterField(
            model_name='source',
            name='due_poll',
            field=models.DateTimeField(default=datetime.datetime(1900, 1, 1, 0, 0)),
        ),
    ]