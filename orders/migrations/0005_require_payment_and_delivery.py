from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_order_payment_delivery'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='metodo_pago',
            field=models.CharField(
                choices=[('efectivo', 'Efectivo'), ('tarjeta', 'Tarjeta')],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='tipo_entrega',
            field=models.CharField(
                choices=[
                    ('domicilio', 'Domicilio'),
                    ('recoger', 'Recoger en tienda'),
                ],
                max_length=20,
            ),
        ),
    ]
