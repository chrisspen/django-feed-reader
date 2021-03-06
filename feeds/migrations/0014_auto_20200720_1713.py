# Generated by Django 2.2.4 on 2020-07-20 21:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0013_auto_20200403_1310'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='subtitle_href',
            field=models.URLField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='subtitle_lang',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='subtitle_type',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.CreateModel(
            name='MediaContent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.URLField(max_length=1000)),
                ('content_type', models.CharField(max_length=50)),
                ('duration', models.IntegerField(blank=True, help_text='Duration of media in seconds.', null=True)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media_content', to='feeds.Post')),
            ],
            options={
                'unique_together': {('post', 'url')},
            },
        ),
    ]
