# Generated manually on 2026-01-07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0052_merge_20260107_0808'),
    ]

    operations = [
        # Alterar o campo para remover a opção 'Semi-reboque'
        # Nota: Os dados já foram convertidos manualmente via shell
        migrations.AlterField(
            model_name='veiculo',
            name='tipo_unidade',
            field=models.CharField(
                choices=[
                    ('Carro', 'Carro'),
                    ('Van', 'Van'),
                    ('Caminhão', 'Caminhão'),
                    ('Cavalo', 'Cavalo'),
                    ('Reboque', 'Reboque'),
                ],
                default='Caminhão',
                max_length=50,
                verbose_name='Tipo da Unidade de Veículo'
            ),
        ),
    ]

