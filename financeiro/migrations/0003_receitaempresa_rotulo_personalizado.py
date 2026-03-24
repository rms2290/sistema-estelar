# Generated manually for fechamento de caixa — entradas personalizadas

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0002_carregamento_fk_cobranca'),
    ]

    operations = [
        migrations.AddField(
            model_name='receitaempresa',
            name='rotulo_personalizado',
            field=models.CharField(
                blank=True,
                help_text='Usado quando o tipo é "Outro": rótulo exibido no fechamento de caixa.',
                max_length=120,
                null=True,
                verbose_name='Nome do campo (fechamento)',
            ),
        ),
    ]
