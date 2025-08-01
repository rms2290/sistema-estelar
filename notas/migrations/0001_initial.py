# Generated by Django 5.2.4 on 2025-07-22 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NotaFiscal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cliente', models.CharField(max_length=200)),
                ('nota', models.CharField(max_length=50, unique=True)),
                ('data', models.DateField()),
                ('fornecedor', models.CharField(max_length=200)),
                ('mercadoria', models.CharField(max_length=200)),
                ('quantidade', models.DecimalField(decimal_places=2, max_digits=10)),
                ('peso', models.DecimalField(decimal_places=2, max_digits=10)),
                ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
            options={
                'verbose_name': 'Nota Fiscal',
                'verbose_name_plural': 'Notas Fiscais',
                'ordering': ['-data', 'nota'],
            },
        ),
    ]
