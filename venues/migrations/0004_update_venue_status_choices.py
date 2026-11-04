from django.db import migrations, models


def migrate_venue_statuses_forward(apps, schema_editor):
    Venue = apps.get_model('venues', 'Venue')
    Venue.objects.filter(
        status__in=['DISPONIBLE', 'RESERVADO'],
    ).update(status='activo')


def migrate_venue_statuses_backward(apps, schema_editor):
    Venue = apps.get_model('venues', 'Venue')
    Venue.objects.filter(status='activo').update(status='DISPONIBLE')
    Venue.objects.filter(status='eliminado').update(status='RESERVADO')


class Migration(migrations.Migration):

    dependencies = [
        ('venues', '0003_remove_venue_imagen'),
    ]

    operations = [
        migrations.RunPython(
            migrate_venue_statuses_forward,
            migrate_venue_statuses_backward,
        ),
        migrations.AlterField(
            model_name='venue',
            name='status',
            field=models.CharField(
                choices=[('activo', 'Activo'), ('eliminado', 'Eliminado')],
                default='activo',
                max_length=10,
            ),
        ),
    ]
