from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0009_sala_notas_liberadas'),
    ]

    operations = [
        migrations.AddField(
            model_name='sala',
            name='tipo_atividade',
            field=models.CharField(
                choices=[('simulacao', 'Simulação'), ('prova', 'Prova')],
                default='simulacao',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='sala',
            name='correcao_automatica',
            field=models.BooleanField(default=False),
        ),
    ]
