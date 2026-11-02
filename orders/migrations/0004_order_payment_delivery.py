from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_alter_order_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='metodo_pago',
            field=models.CharField(
                blank=True,
                choices=[('efectivo', 'Efectivo'), ('tarjeta', 'Tarjeta')],
                default='',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='tipo_entrega',
            field=models.CharField(
                blank=True,
                choices=[
                    ('domicilio', 'Domicilio'),
                    ('recoger', 'Recoger en tienda'),
                ],
                default='',
                max_length=20,
            ),
        ),
    ]
