from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0067_cobrancacteavulsa'),
    ]

    operations = [
        migrations.AddField(
            model_name='cobrancacarregamento',
            name='descricao_avulsa',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Descrição da despesa avulsa'),
        ),
        migrations.AddField(
            model_name='cobrancacarregamento',
            name='origem_cobranca',
            field=models.CharField(
                choices=[('ROMANEIO', 'Com Romaneio'), ('AVULSA_CLIENTE', 'Despesa Avulsa para Cliente')],
                default='ROMANEIO',
                max_length=20,
                verbose_name='Origem da Cobrança',
            ),
        ),
        migrations.AddIndex(
            model_name='cobrancacarregamento',
            index=models.Index(fields=['origem_cobranca'], name='notas_cobra_origem__d8cd74_idx'),
        ),
    ]
