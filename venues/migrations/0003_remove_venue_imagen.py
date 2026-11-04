from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('venues', '0002_remove_venue_capacity'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='venue',
            name='imagen',
        ),
    ]
