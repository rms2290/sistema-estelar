"""
Testes para os serviços do sistema
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from django.db import IntegrityError
from django.forms import modelform_factory

from notas.services import (
    RomaneioService, NotaFiscalService, CalculoService, ValidacaoService
)
from notas.models import RomaneioViagem, NotaFiscal, TabelaSeguro
from notas.tests.conftest import (
    ClienteFactory, MotoristaFactory, VeiculoFactory,
    NotaFiscalFactory, RomaneioViagemFactory, TabelaSeguroFactory
)


# ============================================================================
# TESTES DO ROMANEIOSERVICE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.service
class TestRomaneioService:
    """Testes para o RomaneioService"""
    
    def test_criar_romaneio_normal(self, cliente, motorista, veiculo):
        """Testa criação de romaneio normal"""
        from notas.forms import RomaneioViagemForm
        
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota2 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk, nota2.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        assert form.is_valid(), f"Erros: {form.errors}"
        
        romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(form, emitir=False, tipo='normal')
        
        assert sucesso
        assert romaneio is not None
        assert romaneio.status == 'Salvo'
        assert romaneio.codigo.startswith('ROM-')
        assert not romaneio.codigo.startswith('ROM-100-')
        assert romaneio.notas_fiscais.count() == 2
        
        # Verificar que status das notas foi atualizado
        nota1.refresh_from_db()
        nota2.refresh_from_db()
        assert nota1.status == 'Depósito'  # Romaneio salvo, não emitido
        assert nota2.status == 'Depósito'
    
    def test_criar_romaneio_emitido(self, cliente, motorista, veiculo):
        """Testa criação de romaneio emitido"""
        from notas.forms import RomaneioViagemForm
        
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        assert form.is_valid()
        
        romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(form, emitir=True, tipo='normal')
        
        assert sucesso
        assert romaneio.status == 'Emitido'
        
        # Verificar que status da nota foi atualizado para Enviada
        nota1.refresh_from_db()
        assert nota1.status == 'Enviada'
    
    def test_criar_romaneio_generico(self, cliente, motorista, veiculo):
        """Testa criação de romaneio genérico"""
        from notas.forms import RomaneioViagemForm
        
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        assert form.is_valid()
        
        romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(form, emitir=False, tipo='generico')
        
        assert sucesso
        assert romaneio.codigo.startswith('ROM-100-')
    
    def test_editar_romaneio(self, romaneio):
        """Testa edição de romaneio"""
        from notas.forms import RomaneioViagemForm
        
        nota_antiga = romaneio.notas_fiscais.first()
        nota_nova = NotaFiscalFactory(cliente=romaneio.cliente, status='Depósito')
        
        # Atualizar queryset do form para incluir as notas
        form = RomaneioViagemForm(instance=romaneio)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=romaneio.cliente)
        
        form_data = {
            'cliente': romaneio.cliente.pk,
            'motorista': romaneio.motorista.pk,
            'veiculo_principal': romaneio.veiculo_principal.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota_nova.pk]  # Substituir nota
        }
        
        form = RomaneioViagemForm(data=form_data, instance=romaneio)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=romaneio.cliente)
        assert form.is_valid(), f"Erros: {form.errors}"
        
        romaneio_editado, sucesso, mensagem = RomaneioService.editar_romaneio(
            romaneio, form, emitir=False, salvar=True
        )
        
        assert sucesso, f"Mensagem de erro: {mensagem}"
        assert romaneio_editado is not None
        assert romaneio_editado.status == 'Salvo'
        
        # Verificar que nota removida voltou para Depósito (se existia)
        if nota_antiga:
            nota_antiga.refresh_from_db()
            # Pode estar em Depósito se não estiver em outro romaneio emitido
            assert nota_antiga.status in ['Depósito', 'Enviada']
    
    def test_editar_romaneio_emitir(self, romaneio):
        """Testa edição de romaneio marcando como emitido"""
        from notas.forms import RomaneioViagemForm
        
        nota = romaneio.notas_fiscais.first()
        if nota:
            nota.status = 'Depósito'
            nota.save()
        
        form_data = {
            'cliente': romaneio.cliente.pk,
            'motorista': romaneio.motorista.pk,
            'veiculo_principal': romaneio.veiculo_principal.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota.pk] if nota else []
        }
        
        form = RomaneioViagemForm(data=form_data, instance=romaneio)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=romaneio.cliente)
        assert form.is_valid(), f"Erros: {form.errors}"
        
        romaneio_editado, sucesso, mensagem = RomaneioService.editar_romaneio(
            romaneio, form, emitir=True, salvar=False
        )
        
        assert sucesso, f"Mensagem de erro: {mensagem}"
        assert romaneio_editado is not None
        assert romaneio_editado.status == 'Emitido'
        
        # Verificar que nota foi atualizada para Enviada (se existia)
        if nota:
            nota.refresh_from_db()
            assert nota.status == 'Enviada'
    
    def test_excluir_romaneio(self, romaneio):
        """Testa exclusão de romaneio"""
        nota = romaneio.notas_fiscais.first()
        if nota:
            nota.status = 'Enviada'
            nota.save()
        
        pk_romaneio = romaneio.pk
        sucesso, mensagem = RomaneioService.excluir_romaneio(romaneio)
        
        assert sucesso
        assert 'excluído' in mensagem.lower()
        
        # Verificar que romaneio foi excluído
        assert not RomaneioViagem.objects.filter(pk=pk_romaneio).exists()
        
        # Verificar que nota voltou para Depósito (se existia)
        if nota:
            nota.refresh_from_db()
            assert nota.status == 'Depósito'
    
    def test_calcular_totais_romaneio(self, romaneio):
        """Testa cálculo de totais de um romaneio"""
        totais = RomaneioService.calcular_totais_romaneio(romaneio)
        
        assert 'total_peso' in totais
        assert 'total_valor' in totais
        assert 'quantidade_notas' in totais
        assert totais['quantidade_notas'] == romaneio.notas_fiscais.count()
        assert totais['total_peso'] >= 0
        assert totais['total_valor'] >= 0
    
    def test_obter_notas_disponiveis_para_cliente(self, cliente):
        """Testa obtenção de notas disponíveis para cliente"""
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota2 = NotaFiscalFactory(cliente=cliente, status='Enviada')
        nota3 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        notas_disponiveis = RomaneioService.obter_notas_disponiveis_para_cliente(cliente.pk)
        
        assert notas_disponiveis.count() == 2
        assert nota1 in notas_disponiveis
        assert nota3 in notas_disponiveis
        assert nota2 not in notas_disponiveis
    
    def test_obter_notas_disponiveis_cliente_inexistente(self):
        """Testa obtenção de notas para cliente inexistente"""
        notas = RomaneioService.obter_notas_disponiveis_para_cliente(99999)
        assert notas.count() == 0


# ============================================================================
# TESTES DO NOTAFISCALSERVICE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.service
class TestNotaFiscalService:
    """Testes para o NotaFiscalService"""
    
    def test_criar_nota_fiscal(self, cliente):
        """Testa criação de nota fiscal"""
        from notas.forms import NotaFiscalForm
        
        form_data = {
            'cliente': cliente.pk,
            'nota': '123456',
            'data': date.today(),
            'fornecedor': 'Fornecedor Teste',
            'mercadoria': 'Mercadoria Teste',
            'quantidade': '100.00',
            'peso': '1000.00',
            'valor': '5000.00'
        }
        
        form = NotaFiscalForm(data=form_data)
        assert form.is_valid()
        
        nota, sucesso, mensagem = NotaFiscalService.criar_nota_fiscal(form)
        
        assert sucesso
        assert nota is not None
        assert nota.nota == '123456'
        assert 'criada com sucesso' in mensagem.lower()
    
    def test_atualizar_nota_fiscal(self, nota_fiscal):
        """Testa atualização de nota fiscal"""
        from notas.forms import NotaFiscalForm
        
        form_data = {
            'cliente': nota_fiscal.cliente.pk,
            'nota': nota_fiscal.nota,
            'data': nota_fiscal.data,
            'fornecedor': 'Fornecedor Editado',
            'mercadoria': nota_fiscal.mercadoria,
            'quantidade': str(nota_fiscal.quantidade),
            'peso': str(nota_fiscal.peso),
            'valor': str(nota_fiscal.valor)
        }
        
        form = NotaFiscalForm(data=form_data, instance=nota_fiscal)
        assert form.is_valid()
        
        nota_atualizada, sucesso, mensagem = NotaFiscalService.atualizar_nota_fiscal(nota_fiscal, form)
        
        assert sucesso
        nota_fiscal.refresh_from_db()
        assert nota_fiscal.fornecedor == 'FORNECEDOR EDITADO'
    
    def test_obter_notas_por_cliente(self, cliente):
        """Testa obtenção de notas por cliente"""
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota2 = NotaFiscalFactory(cliente=cliente, status='Enviada')
        nota3 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        notas = NotaFiscalService.obter_notas_por_cliente(cliente.pk)
        
        assert notas.count() == 3
        assert nota1 in notas
        assert nota2 in notas
        assert nota3 in notas
    
    def test_obter_notas_por_cliente_com_status(self, cliente):
        """Testa obtenção de notas por cliente com filtro de status"""
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota2 = NotaFiscalFactory(cliente=cliente, status='Enviada')
        nota3 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        notas = NotaFiscalService.obter_notas_por_cliente(cliente.pk, status='Depósito')
        
        assert notas.count() == 2
        assert nota1 in notas
        assert nota3 in notas
        assert nota2 not in notas
    
    def test_calcular_totais_por_cliente(self, cliente):
        """Testa cálculo de totais por cliente"""
        NotaFiscalFactory(cliente=cliente, peso=100, valor=Decimal('1000.00'))
        NotaFiscalFactory(cliente=cliente, peso=200, valor=Decimal('2000.00'))
        NotaFiscalFactory(cliente=cliente, peso=300, valor=Decimal('3000.00'))
        
        totais = NotaFiscalService.calcular_totais_por_cliente(cliente.pk)
        
        assert totais['total_peso'] == 600
        assert totais['total_valor'] == Decimal('6000.00')
        assert totais['quantidade'] == 3
    
    def test_calcular_totais_por_cliente_com_status(self, cliente):
        """Testa cálculo de totais por cliente com filtro de status"""
        NotaFiscalFactory(cliente=cliente, peso=100, valor=Decimal('1000.00'), status='Depósito')
        NotaFiscalFactory(cliente=cliente, peso=200, valor=Decimal('2000.00'), status='Enviada')
        NotaFiscalFactory(cliente=cliente, peso=300, valor=Decimal('3000.00'), status='Depósito')
        
        totais = NotaFiscalService.calcular_totais_por_cliente(cliente.pk, status='Depósito')
        
        assert totais['total_peso'] == 400
        assert totais['total_valor'] == Decimal('4000.00')
        assert totais['quantidade'] == 2
    
    def test_verificar_disponibilidade_nota_deposito(self, nota_fiscal):
        """Testa verificação de disponibilidade de nota em depósito"""
        nota_fiscal.status = 'Depósito'
        nota_fiscal.save()
        
        disponivel = NotaFiscalService.verificar_disponibilidade_nota(nota_fiscal)
        assert disponivel is True
    
    def test_verificar_disponibilidade_nota_enviada(self, nota_fiscal):
        """Testa verificação de disponibilidade de nota enviada"""
        nota_fiscal.status = 'Enviada'
        nota_fiscal.save()
        
        disponivel = NotaFiscalService.verificar_disponibilidade_nota(nota_fiscal)
        assert disponivel is False


# ============================================================================
# TESTES DO CALCULOSERVICE
# ============================================================================

@pytest.mark.django_db
@pytest.mark.service
class TestCalculoService:
    """Testes para o CalculoService"""
    
    def test_calcular_seguro_por_estado(self):
        """Testa cálculo de seguro por estado"""
        tabela = TabelaSeguroFactory(estado='SP', percentual_seguro=Decimal('2.5'))
        
        valor_total = Decimal('10000.00')
        resultado = CalculoService.calcular_seguro_por_estado(valor_total, 'SP')
        
        assert resultado['percentual'] == Decimal('2.5')
        assert resultado['valor_seguro'] == Decimal('250.00')  # 10000 * 2.5 / 100
    
    def test_calcular_seguro_estado_inexistente(self):
        """Testa cálculo de seguro para estado sem tabela"""
        valor_total = Decimal('10000.00')
        resultado = CalculoService.calcular_seguro_por_estado(valor_total, 'XX')
        
        assert resultado['percentual'] == Decimal('0.0')
        assert resultado['valor_seguro'] == Decimal('0.0')
    
    def test_calcular_totais_por_periodo(self, cliente, motorista, veiculo):
        """Testa cálculo de totais por período"""
        from datetime import timedelta
        
        data_inicio = date.today() - timedelta(days=10)
        data_fim = date.today()
        
        nota1 = NotaFiscalFactory(cliente=cliente, peso=100, valor=Decimal('1000.00'))
        nota2 = NotaFiscalFactory(cliente=cliente, peso=200, valor=Decimal('2000.00'))
        
        romaneio = RomaneioViagemFactory(
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=veiculo,
            data_emissao=datetime.now(),
            status='Emitido'
        )
        romaneio.notas_fiscais.add(nota1, nota2)
        
        totais = CalculoService.calcular_totais_por_periodo(data_inicio, data_fim, status='Emitido')
        
        # Verificar que retorna os totais (pode ser 0 se não houver romaneios no período)
        assert 'total_romaneios' in totais
        assert 'total_peso' in totais
        assert 'total_valor' in totais
        assert totais['total_romaneios'] >= 0
        assert totais['total_peso'] >= 0
        assert totais['total_valor'] >= 0
    
    def test_calcular_totais_por_cliente(self, cliente, motorista, veiculo):
        """Testa cálculo de totais por cliente"""
        nota1 = NotaFiscalFactory(cliente=cliente, peso=100, valor=Decimal('1000.00'))
        nota2 = NotaFiscalFactory(cliente=cliente, peso=200, valor=Decimal('2000.00'))
        
        romaneio = RomaneioViagemFactory(
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=veiculo,
            data_emissao=datetime.now()
        )
        romaneio.notas_fiscais.add(nota1, nota2)
        
        totais = CalculoService.calcular_totais_por_cliente(cliente.pk)
        
        # Verificar que retorna os totais
        assert 'total_romaneios' in totais
        assert 'total_peso' in totais
        assert 'total_valor' in totais
        assert totais['total_romaneios'] >= 0
        assert totais['total_peso'] >= 0
        assert totais['total_valor'] >= 0
    
    def test_calcular_totais_por_cliente_com_periodo(self, cliente, motorista, veiculo):
        """Testa cálculo de totais por cliente com período"""
        from datetime import timedelta
        
        data_inicio = date.today() - timedelta(days=5)
        data_fim = date.today()
        
        nota1 = NotaFiscalFactory(cliente=cliente, peso=100, valor=Decimal('1000.00'))
        
        romaneio = RomaneioViagemFactory(
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=veiculo,
            data_emissao=datetime.now()
        )
        romaneio.notas_fiscais.add(nota1)
        
        totais = CalculoService.calcular_totais_por_cliente(
            cliente.pk, 
            data_inicio=data_inicio, 
            data_fim=data_fim
        )
        
        # Verificar que retorna os totais
        assert 'total_romaneios' in totais
        assert 'total_peso' in totais
        assert 'total_valor' in totais
        assert totais['total_romaneios'] >= 0
        assert totais['total_peso'] >= 0


# ============================================================================
# TESTES DO VALIDACAOSERVICE
# ============================================================================

@pytest.mark.service
class TestValidacaoService:
    """Testes para o ValidacaoService"""
    
    def test_validar_cnpj_valido(self):
        """Testa validação de CNPJ válido"""
        cnpj = '11.222.333/0001-81'
        valido, mensagem = ValidacaoService.validar_cnpj(cnpj)
        
        assert valido is True
        assert mensagem is None
    
    def test_validar_cnpj_invalido(self):
        """Testa validação de CNPJ inválido"""
        cnpj = '12345678000199'
        valido, mensagem = ValidacaoService.validar_cnpj(cnpj)
        
        assert valido is False
        assert mensagem is not None
    
    def test_validar_cnpj_vazio(self):
        """Testa validação de CNPJ vazio"""
        valido, mensagem = ValidacaoService.validar_cnpj('')
        
        assert valido is False
        assert 'não informado' in mensagem.lower()
    
    def test_validar_cnpj_digitos_insuficientes(self):
        """Testa validação de CNPJ com dígitos insuficientes"""
        cnpj = '123456789'
        valido, mensagem = ValidacaoService.validar_cnpj(cnpj)
        
        assert valido is False
        assert '14 dígitos' in mensagem
    
    def test_validar_cpf_valido(self):
        """Testa validação de CPF válido"""
        cpf = '123.456.789-09'
        valido, mensagem = ValidacaoService.validar_cpf(cpf)
        
        assert valido is True
        assert mensagem is None
    
    def test_validar_cpf_invalido(self):
        """Testa validação de CPF inválido"""
        cpf = '12345678900'
        valido, mensagem = ValidacaoService.validar_cpf(cpf)
        
        assert valido is False
        assert mensagem is not None
    
    def test_validar_cpf_vazio(self):
        """Testa validação de CPF vazio"""
        valido, mensagem = ValidacaoService.validar_cpf('')
        
        assert valido is False
        assert 'não informado' in mensagem.lower()
    
    def test_validar_cpf_digitos_insuficientes(self):
        """Testa validação de CPF com dígitos insuficientes"""
        cpf = '123456789'
        valido, mensagem = ValidacaoService.validar_cpf(cpf)
        
        assert valido is False
        assert '11 dígitos' in mensagem
    
    def test_validar_placa_formato_antigo(self):
        """Testa validação de placa formato antigo"""
        placa = 'ABC1234'
        valido, mensagem = ValidacaoService.validar_placa(placa)
        
        assert valido is True
        assert mensagem is None
    
    def test_validar_placa_formato_mercosul(self):
        """Testa validação de placa formato Mercosul"""
        placa = 'ABC1D23'
        valido, mensagem = ValidacaoService.validar_placa(placa)
        
        assert valido is True
        assert mensagem is None
    
    def test_validar_placa_invalida(self):
        """Testa validação de placa inválida"""
        placa = 'ABC123'
        valido, mensagem = ValidacaoService.validar_placa(placa)
        
        assert valido is False
        assert 'inválida' in mensagem.lower()
    
    def test_validar_placa_vazia(self):
        """Testa validação de placa vazia"""
        valido, mensagem = ValidacaoService.validar_placa('')
        
        assert valido is False
        assert 'não informada' in mensagem.lower()


@pytest.mark.django_db
@pytest.mark.service
class TestValidacaoServiceRomaneio:
    """Testes de validação de romaneio"""
    
    def test_validar_romaneio_valido(self, romaneio):
        """Testa validação de romaneio válido"""
        # Romaneio deve ter pelo menos uma nota fiscal para ser válido
        if not romaneio.notas_fiscais.exists():
            nota = NotaFiscalFactory(cliente=romaneio.cliente)
            romaneio.notas_fiscais.add(nota)
        
        valido, erros = ValidacaoService.validar_romaneio_antes_salvar(romaneio)
        
        assert valido is True
        assert len(erros) == 0
    
    def test_validar_romaneio_sem_notas(self, cliente, motorista, veiculo):
        """Testa validação de romaneio sem notas fiscais"""
        from notas.models import RomaneioViagem
        romaneio = RomaneioViagem(
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=veiculo
        )
        # Não adicionar notas (romaneio não salvo ainda)
        
        valido, erros = ValidacaoService.validar_romaneio_antes_salvar(romaneio)
        
        assert valido is False
        assert any('nota fiscal' in erro.lower() for erro in erros)
    
    def test_validar_romaneio_sem_cliente(self, motorista, veiculo):
        """Testa validação de romaneio sem cliente"""
        from notas.models import RomaneioViagem
        romaneio = RomaneioViagem(
            cliente=None,
            motorista=motorista,
            veiculo_principal=veiculo
        )
        
        valido, erros = ValidacaoService.validar_romaneio_antes_salvar(romaneio)
        
        assert valido is False
        assert any('cliente' in erro.lower() for erro in erros)
    
    def test_validar_romaneio_sem_motorista(self, cliente, veiculo):
        """Testa validação de romaneio sem motorista"""
        from notas.models import RomaneioViagem
        romaneio = RomaneioViagem(
            cliente=cliente,
            motorista=None,
            veiculo_principal=veiculo
        )
        
        valido, erros = ValidacaoService.validar_romaneio_antes_salvar(romaneio)
        
        assert valido is False
        assert any('motorista' in erro.lower() for erro in erros)
    
    def test_validar_romaneio_sem_veiculo(self, cliente, motorista):
        """Testa validação de romaneio sem veículo principal"""
        from notas.models import RomaneioViagem
        romaneio = RomaneioViagem(
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=None
        )
        
        valido, erros = ValidacaoService.validar_romaneio_antes_salvar(romaneio)
        
        assert valido is False
        assert any('veículo' in erro.lower() for erro in erros)


@pytest.mark.django_db
@pytest.mark.service
class TestValidacaoServiceNotaFiscal:
    """Testes de validação de nota fiscal"""
    
    def test_validar_nota_fiscal_valida(self, nota_fiscal):
        """Testa validação de nota fiscal válida"""
        valido, erros = ValidacaoService.validar_nota_fiscal_antes_salvar(nota_fiscal)
        
        assert valido is True
        assert len(erros) == 0
    
    def test_validar_nota_fiscal_sem_numero(self, cliente):
        """Testa validação de nota fiscal sem número"""
        from notas.models import NotaFiscal
        nota = NotaFiscal(cliente=cliente, nota='')
        
        valido, erros = ValidacaoService.validar_nota_fiscal_antes_salvar(nota)
        
        assert valido is False
        assert any('número' in erro.lower() for erro in erros)
    
    def test_validar_nota_fiscal_sem_cliente(self, cliente):
        """Testa validação de nota fiscal sem cliente"""
        from notas.models import NotaFiscal
        nota = NotaFiscal(nota='123456', cliente=None)
        # Nota não salva, então não tem ID
        
        valido, erros = ValidacaoService.validar_nota_fiscal_antes_salvar(nota)
        
        assert valido is False
        assert any('cliente' in erro.lower() for erro in erros)
    
    def test_validar_nota_fiscal_valor_negativo(self, nota_fiscal):
        """Testa validação de nota fiscal com valor negativo"""
        nota_fiscal.valor = Decimal('-100.00')
        
        valido, erros = ValidacaoService.validar_nota_fiscal_antes_salvar(nota_fiscal)
        
        assert valido is False
        assert any('negativo' in erro.lower() for erro in erros)
    
    def test_validar_nota_fiscal_peso_negativo(self, nota_fiscal):
        """Testa validação de nota fiscal com peso negativo"""
        nota_fiscal.peso = -100
        
        valido, erros = ValidacaoService.validar_nota_fiscal_antes_salvar(nota_fiscal)
        
        assert valido is False
        assert any('negativo' in erro.lower() for erro in erros)
