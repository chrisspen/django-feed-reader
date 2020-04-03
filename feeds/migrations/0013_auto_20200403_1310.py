# Generated by Django 2.2.4 on 2020-04-03 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0012_auto_20200310_0913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='source',
            name='feed_url',
            field=models.CharField(max_length=1000),
        ),
        migrations.AlterField(
            model_name='source',
            name='image_url',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='last_302_url',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AlterField(
            model_name='source',
            name='site_url',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]