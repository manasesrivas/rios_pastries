from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_require_payment_and_delivery'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='idempotency_key',
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='request_fingerprint',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
    ]
