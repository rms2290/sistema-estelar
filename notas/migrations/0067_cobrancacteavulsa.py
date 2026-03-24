from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notas', '0066_cobrancacarregamento_data_pagamento_cte_terceiro_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CobrancaCTEAvulsa',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome')),
                ('valor_cte_manifesto', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Valor CTE/Manifesto (R$)')),
                ('valor_cte_terceiro', models.DecimalField(decimal_places=2, default=0.0, max_digits=10, verbose_name='Valor CTE/Terceiro (R$)')),
                ('status', models.CharField(choices=[('Pendente', 'Pendente'), ('Baixado', 'Baixado')], default='Pendente', max_length=10, verbose_name='Status (A Receber)')),
                ('data_baixa', models.DateField(blank=True, null=True, verbose_name='Data de Baixa')),
                ('status_cte_terceiro', models.CharField(choices=[('Pendente', 'Pendente'), ('Pago', 'Pago')], default='Pendente', max_length=10, verbose_name='Status CTE/Terceiro')),
                ('data_pagamento_cte_terceiro', models.DateField(blank=True, null=True, verbose_name='Data de Pagamento CTE/Terceiro')),
                ('observacoes', models.TextField(blank=True, null=True, verbose_name='Observações')),
                ('criado_em', models.DateTimeField(auto_now_add=True, verbose_name='Data de Criação')),
                ('atualizado_em', models.DateTimeField(auto_now=True, verbose_name='Data de Atualização')),
            ],
            options={
                'verbose_name': 'Cobrança CTE Avulsa',
                'verbose_name_plural': 'Cobranças CTE Avulsas',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.AddIndex(
            model_name='cobrancacteavulsa',
            index=models.Index(fields=['status'], name='notas_cobra_status_3ca3f6_idx'),
        ),
        migrations.AddIndex(
            model_name='cobrancacteavulsa',
            index=models.Index(fields=['status_cte_terceiro'], name='notas_cobra_status__c3949f_idx'),
        ),
        migrations.AddIndex(
            model_name='cobrancacteavulsa',
            index=models.Index(fields=['-criado_em'], name='notas_cobra_criado__8d6ef1_idx'),
        ),
    ]
