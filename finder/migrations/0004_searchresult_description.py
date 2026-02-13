from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finder", "0003_productimage_detected_labels"),
    ]

    operations = [
        migrations.AddField(
            model_name="searchresult",
            name="description",
            field=models.TextField(blank=True),
        ),
    ]
