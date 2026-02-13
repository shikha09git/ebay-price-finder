from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("finder", "0002_listingproduct"),
    ]

    operations = [
        migrations.AddField(
            model_name="productimage",
            name="detected_labels",
            field=models.TextField(blank=True),
        ),
    ]
