from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0003_rename_categories_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='status',
            field=models.CharField(
                choices=[('activo', 'Activo'), ('eliminado', 'Eliminado')],
                default='activo',
                max_length=10,
            ),
        ),
    ]
