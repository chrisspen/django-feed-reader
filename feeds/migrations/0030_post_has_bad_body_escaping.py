from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0029_source_extract_from_raw_html_page_key_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='has_bad_body_escaping',
            field=models.BooleanField(db_index=True, default=None, null=True),
        ),
    ]
