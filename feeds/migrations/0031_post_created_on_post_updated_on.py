from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0030_post_has_bad_body_escaping'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='created_on',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='updated_on',
            field=models.DateTimeField(blank=True, editable=False, null=True),
        ),
    ]
