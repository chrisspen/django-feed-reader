# Generated by Django 2.2.4 on 2022-02-14 15:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0018_auto_20220213_2310'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='guid',
            field=models.CharField(blank=True, db_index=True, max_length=2000, null=True),
        ),
    ]
