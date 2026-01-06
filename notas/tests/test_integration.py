"""
Testes de integração - Fluxos completos do sistema
"""
import pytest
from decimal import Decimal
from datetime import date, datetime
from django.urls import reverse
from django.contrib.auth import get_user_model

from notas.models import Cliente, NotaFiscal, RomaneioViagem, Motorista, Veiculo
from notas.services import RomaneioService, NotaFiscalService
from notas.tests.conftest import (
    ClienteFactory, MotoristaFactory, VeiculoFactory,
    NotaFiscalFactory, UsuarioFactory
)

Usuario = get_user_model()


# ============================================================================
# FLUXO COMPLETO: CRIAR CLIENTE -> NOTA FISCAL -> ROMANEIO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestFluxoCompletoRomaneio:
    """Testa fluxo completo de criação de romaneio"""
    
    def test_fluxo_completo_criar_romaneio(self):
        """Testa fluxo completo: Cliente -> Nota Fiscal -> Romaneio"""
        # 1. Criar cliente
        cliente = ClienteFactory(
            razao_social='Empresa Teste LTDA',
            cnpj='11222333000181',
            status='Ativo'
        )
        assert Cliente.objects.filter(pk=cliente.pk).exists()
        
        # 2. Criar notas fiscais para o cliente
        nota1 = NotaFiscalFactory(
            cliente=cliente,
            nota='NF001',
            peso=100,
            valor=Decimal('1000.00'),
            status='Depósito'
        )
        nota2 = NotaFiscalFactory(
            cliente=cliente,
            nota='NF002',
            peso=200,
            valor=Decimal('2000.00'),
            status='Depósito'
        )
        
        assert nota1.status == 'Depósito'
        assert nota2.status == 'Depósito'
        
        # 3. Criar motorista e veículo
        motorista = MotoristaFactory()
        veiculo = VeiculoFactory()
        
        # 4. Criar romaneio vinculando as notas
        from notas.forms import RomaneioViagemForm
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk, nota2.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form.is_valid(), f"Erros: {form.errors}"
        
        romaneio, sucesso, mensagem = RomaneioService.criar_romaneio(form, emitir=True, tipo='normal')
        
        assert sucesso
        assert romaneio is not None
        assert romaneio.status == 'Emitido'
        assert romaneio.notas_fiscais.count() == 2
        
        # 5. Verificar que status das notas foi atualizado
        nota1.refresh_from_db()
        nota2.refresh_from_db()
        assert nota1.status == 'Enviada'
        assert nota2.status == 'Enviada'
        
        # 6. Verificar totais do romaneio
        totais = RomaneioService.calcular_totais_romaneio(romaneio)
        assert totais['total_peso'] == 300
        assert totais['total_valor'] == Decimal('3000.00')
        assert totais['quantidade_notas'] == 2


# ============================================================================
# FLUXO: CRIAR E EDITAR ROMANEIO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestFluxoEditarRomaneio:
    """Testa fluxo de edição de romaneio"""
    
    def test_fluxo_editar_romaneio_adicionar_nota(self, cliente, motorista, veiculo):
        """Testa edição de romaneio adicionando nova nota"""
        # 1. Criar notas fiscais
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota2 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota3 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        # 2. Criar romaneio com nota1
        from notas.forms import RomaneioViagemForm
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form.is_valid()
        
        romaneio, sucesso, _ = RomaneioService.criar_romaneio(form, emitir=False, tipo='normal')
        assert sucesso
        assert romaneio.notas_fiscais.count() == 1
        
        # 3. Editar romaneio adicionando nota2 e nota3
        # Atualizar data_emissao do romaneio para datetime se necessário
        if isinstance(romaneio.data_emissao, date):
            from datetime import datetime
            romaneio.data_emissao = datetime.combine(romaneio.data_emissao, datetime.min.time())
            romaneio.save()
        
        form_data_edit = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk, nota2.pk, nota3.pk]
        }
        
        form_edit = RomaneioViagemForm(data=form_data_edit, instance=romaneio)
        form_edit.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form_edit.is_valid(), f"Erros: {form_edit.errors}"
        
        romaneio_editado, sucesso_edit, _ = RomaneioService.editar_romaneio(
            romaneio, form_edit, emitir=False, salvar=True
        )
        
        assert sucesso_edit
        assert romaneio_editado.notas_fiscais.count() == 3
        assert nota1 in romaneio_editado.notas_fiscais.all()
        assert nota2 in romaneio_editado.notas_fiscais.all()
        assert nota3 in romaneio_editado.notas_fiscais.all()
    
    def test_fluxo_editar_romaneio_remover_nota(self, cliente, motorista, veiculo):
        """Testa edição de romaneio removendo nota"""
        # 1. Criar notas fiscais
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota2 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        # 2. Criar romaneio com ambas as notas
        from notas.forms import RomaneioViagemForm
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk, nota2.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form.is_valid()
        
        romaneio, sucesso, _ = RomaneioService.criar_romaneio(form, emitir=True, tipo='normal')
        assert sucesso
        
        # Verificar que notas estão como Enviada
        nota1.refresh_from_db()
        nota2.refresh_from_db()
        assert nota1.status == 'Enviada'
        assert nota2.status == 'Enviada'
        
        # 3. Editar romaneio removendo nota2
        # Atualizar data_emissao do romaneio para datetime se necessário
        if isinstance(romaneio.data_emissao, date):
            from datetime import datetime
            romaneio.data_emissao = datetime.combine(romaneio.data_emissao, datetime.min.time())
            romaneio.save()
        
        form_data_edit = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk]  # Apenas nota1
        }
        
        form_edit = RomaneioViagemForm(data=form_data_edit, instance=romaneio)
        form_edit.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form_edit.is_valid(), f"Erros: {form_edit.errors}"
        
        romaneio_editado, sucesso_edit, _ = RomaneioService.editar_romaneio(
            romaneio, form_edit, emitir=False, salvar=True
        )
        
        assert sucesso_edit
        assert romaneio_editado.notas_fiscais.count() == 1
        assert nota1 in romaneio_editado.notas_fiscais.all()
        assert nota2 not in romaneio_editado.notas_fiscais.all()
        
        # Verificar que nota2 voltou para Depósito
        nota2.refresh_from_db()
        assert nota2.status == 'Depósito'


# ============================================================================
# FLUXO: EXCLUIR ROMANEIO E ATUALIZAR STATUS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestFluxoExcluirRomaneio:
    """Testa fluxo de exclusão de romaneio"""
    
    def test_fluxo_excluir_romaneio_atualiza_notas(self, cliente, motorista, veiculo):
        """Testa que exclusão de romaneio atualiza status das notas"""
        # 1. Criar notas fiscais
        nota1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota2 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        # 2. Criar romaneio emitido
        from notas.forms import RomaneioViagemForm
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk, nota2.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form.is_valid()
        
        romaneio, sucesso, _ = RomaneioService.criar_romaneio(form, emitir=True, tipo='normal')
        assert sucesso
        
        # Verificar que notas estão como Enviada
        nota1.refresh_from_db()
        nota2.refresh_from_db()
        assert nota1.status == 'Enviada'
        assert nota2.status == 'Enviada'
        
        # 3. Excluir romaneio
        pk_romaneio = romaneio.pk
        sucesso_excluir, mensagem = RomaneioService.excluir_romaneio(romaneio)
        
        assert sucesso_excluir
        assert not RomaneioViagem.objects.filter(pk=pk_romaneio).exists()
        
        # 4. Verificar que notas voltaram para Depósito
        nota1.refresh_from_db()
        nota2.refresh_from_db()
        assert nota1.status == 'Depósito'
        assert nota2.status == 'Depósito'


# ============================================================================
# FLUXO: NOTA FISCAL EM MÚLTIPLOS ROMANEIOS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestFluxoNotaMultiplosRomaneios:
    """Testa comportamento de nota fiscal em múltiplos romaneios"""
    
    def test_nota_fiscal_em_dois_romaneios_emitidos(self, cliente, motorista, veiculo):
        """Testa que nota em dois romaneios emitidos permanece como Enviada"""
        # 1. Criar nota fiscal
        nota = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        # 2. Criar primeiro romaneio emitido
        from notas.forms import RomaneioViagemForm
        
        form_data1 = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota.pk]
        }
        
        form1 = RomaneioViagemForm(data=form_data1)
        form1.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form1.is_valid()
        
        romaneio1, sucesso1, _ = RomaneioService.criar_romaneio(form1, emitir=True, tipo='normal')
        assert sucesso1
        
        # Verificar que nota está como Enviada
        nota.refresh_from_db()
        assert nota.status == 'Enviada'
        
        # 3. Criar segundo romaneio emitido com a mesma nota
        form_data2 = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota.pk]
        }
        
        form2 = RomaneioViagemForm(data=form_data2)
        form2.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form2.is_valid()
        
        romaneio2, sucesso2, _ = RomaneioService.criar_romaneio(form2, emitir=True, tipo='normal')
        assert sucesso2
        
        # Verificar que nota permanece como Enviada
        nota.refresh_from_db()
        assert nota.status == 'Enviada'
        
        # 4. Excluir primeiro romaneio
        RomaneioService.excluir_romaneio(romaneio1)
        
        # Verificar que nota ainda está como Enviada (porque está no romaneio2)
        nota.refresh_from_db()
        assert nota.status == 'Enviada'
        
        # 5. Excluir segundo romaneio
        RomaneioService.excluir_romaneio(romaneio2)
        
        # Agora nota deve voltar para Depósito
        nota.refresh_from_db()
        assert nota.status == 'Depósito'


# ============================================================================
# FLUXO: CRIAR NOTA FISCAL E ADICIONAR A ROMANEIO
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestFluxoNotaFiscalRomaneio:
    """Testa fluxo de criação de nota fiscal e adição a romaneio"""
    
    def test_fluxo_criar_nota_e_adicionar_romaneio(self, cliente, motorista, veiculo):
        """Testa criar nota fiscal e adicionar a romaneio"""
        # 1. Criar nota fiscal
        from notas.forms import NotaFiscalForm
        
        form_data_nota = {
            'cliente': cliente.pk,
            'nota': 'NF123',
            'data': date.today(),
            'fornecedor': 'Fornecedor Teste',
            'mercadoria': 'Mercadoria Teste',
            'quantidade': '100.00',
            'peso': '1000.00',
            'valor': '5000.00'
        }
        
        form_nota = NotaFiscalForm(data=form_data_nota)
        assert form_nota.is_valid()
        
        nota, sucesso_nota, _ = NotaFiscalService.criar_nota_fiscal(form_nota)
        assert sucesso_nota
        assert nota.status == 'Depósito'  # Status padrão
        
        # 2. Verificar que nota está disponível
        disponivel = NotaFiscalService.verificar_disponibilidade_nota(nota)
        assert disponivel is True
        
        # 3. Criar romaneio com a nota
        from notas.forms import RomaneioViagemForm
        
        form_data_romaneio = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota.pk]
        }
        
        form_romaneio = RomaneioViagemForm(data=form_data_romaneio)
        form_romaneio.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form_romaneio.is_valid()
        
        romaneio, sucesso_romaneio, _ = RomaneioService.criar_romaneio(
            form_romaneio, emitir=True, tipo='normal'
        )
        
        assert sucesso_romaneio
        assert romaneio.notas_fiscais.count() == 1
        assert nota in romaneio.notas_fiscais.all()
        
        # 4. Verificar que status da nota foi atualizado
        nota.refresh_from_db()
        assert nota.status == 'Enviada'
        
        # 5. Verificar que nota não está mais disponível
        disponivel_depois = NotaFiscalService.verificar_disponibilidade_nota(nota)
        assert disponivel_depois is False


# ============================================================================
# FLUXO: CALCULAR TOTAIS E ESTATÍSTICAS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestFluxoCalculosEstatisticas:
    """Testa fluxo de cálculos e estatísticas"""
    
    def test_fluxo_calcular_totais_cliente(self, cliente, motorista, veiculo):
        """Testa cálculo de totais por cliente"""
        # 1. Criar múltiplas notas fiscais
        nota1 = NotaFiscalFactory(cliente=cliente, peso=100, valor=Decimal('1000.00'))
        nota2 = NotaFiscalFactory(cliente=cliente, peso=200, valor=Decimal('2000.00'))
        nota3 = NotaFiscalFactory(cliente=cliente, peso=300, valor=Decimal('3000.00'))
        
        # 2. Calcular totais
        totais = NotaFiscalService.calcular_totais_por_cliente(cliente.pk)
        
        assert totais['total_peso'] == 600
        assert totais['total_valor'] == Decimal('6000.00')
        assert totais['quantidade'] == 3
        
        # 3. Calcular totais apenas de notas em depósito
        nota1.status = 'Depósito'
        nota1.save()
        nota2.status = 'Enviada'
        nota2.save()
        nota3.status = 'Depósito'
        nota3.save()
        
        totais_deposito = NotaFiscalService.calcular_totais_por_cliente(cliente.pk, status='Depósito')
        
        assert totais_deposito['total_peso'] == 400  # nota1 + nota3
        assert totais_deposito['total_valor'] == Decimal('4000.00')
        assert totais_deposito['quantidade'] == 2
    
    def test_fluxo_calcular_totais_romaneio(self, cliente, motorista, veiculo):
        """Testa cálculo de totais de romaneio"""
        # 1. Criar notas fiscais
        nota1 = NotaFiscalFactory(cliente=cliente, peso=100, valor=Decimal('1000.00'))
        nota2 = NotaFiscalFactory(cliente=cliente, peso=200, valor=Decimal('2000.00'))
        
        # 2. Criar romaneio
        from notas.forms import RomaneioViagemForm
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota1.pk, nota2.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form.is_valid()
        
        romaneio, sucesso, _ = RomaneioService.criar_romaneio(form, emitir=False, tipo='normal')
        assert sucesso
        
        # 3. Calcular totais do romaneio
        totais = RomaneioService.calcular_totais_romaneio(romaneio)
        
        assert totais['total_peso'] == 300
        assert totais['total_valor'] == Decimal('3000.00')
        assert totais['quantidade_notas'] == 2


# ============================================================================
# FLUXO: BUSCAR NOTAS DISPONÍVEIS
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestFluxoBuscarNotasDisponiveis:
    """Testa fluxo de busca de notas disponíveis"""
    
    def test_fluxo_buscar_notas_disponiveis_cliente(self, cliente):
        """Testa busca de notas disponíveis para cliente"""
        # 1. Criar notas com diferentes status
        nota_deposito1 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota_deposito2 = NotaFiscalFactory(cliente=cliente, status='Depósito')
        nota_enviada = NotaFiscalFactory(cliente=cliente, status='Enviada')
        
        # 2. Buscar notas disponíveis
        notas_disponiveis = RomaneioService.obter_notas_disponiveis_para_cliente(cliente.pk)
        
        assert notas_disponiveis.count() == 2
        assert nota_deposito1 in notas_disponiveis
        assert nota_deposito2 in notas_disponiveis
        assert nota_enviada not in notas_disponiveis
        
        # 3. Adicionar nota_deposito1 a um romaneio emitido
        from notas.forms import RomaneioViagemForm
        motorista = MotoristaFactory()
        veiculo = VeiculoFactory()
        
        form_data = {
            'cliente': cliente.pk,
            'motorista': motorista.pk,
            'veiculo_principal': veiculo.pk,
            'data_romaneio': date.today(),
            'notas_fiscais': [nota_deposito1.pk]
        }
        
        form = RomaneioViagemForm(data=form_data)
        form.fields['notas_fiscais'].queryset = NotaFiscal.objects.filter(cliente=cliente)
        assert form.is_valid()
        
        romaneio, sucesso, _ = RomaneioService.criar_romaneio(form, emitir=True, tipo='normal')
        assert sucesso
        
        # 4. Verificar que nota_deposito1 não está mais disponível
        notas_disponiveis_depois = RomaneioService.obter_notas_disponiveis_para_cliente(cliente.pk)
        
        assert notas_disponiveis_depois.count() == 1
        assert nota_deposito2 in notas_disponiveis_depois
        assert nota_deposito1 not in notas_disponiveis_depois


# ============================================================================
# FLUXO: VALIDAÇÕES EM CADEIA
# ============================================================================

@pytest.mark.django_db
@pytest.mark.integration
class TestFluxoValidacoes:
    """Testa fluxo de validações em cadeia"""
    
    def test_fluxo_validar_romaneio_completo(self, cliente, motorista, veiculo):
        """Testa validação completa de romaneio"""
        from notas.services import ValidacaoService
        from notas.models import RomaneioViagem
        
        # 1. Criar nota fiscal
        nota = NotaFiscalFactory(cliente=cliente, status='Depósito')
        
        # 2. Criar romaneio válido
        romaneio = RomaneioViagem(
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=veiculo
        )
        romaneio.save()
        romaneio.notas_fiscais.add(nota)
        
        # 3. Validar romaneio
        valido, erros = ValidacaoService.validar_romaneio_antes_salvar(romaneio)
        
        assert valido is True
        assert len(erros) == 0
        
        # 4. Remover nota e validar novamente
        romaneio.notas_fiscais.remove(nota)
        valido_sem_nota, erros_sem_nota = ValidacaoService.validar_romaneio_antes_salvar(romaneio)
        
        assert valido_sem_nota is False
        assert any('nota fiscal' in erro.lower() for erro in erros_sem_nota)
    
    def test_fluxo_validar_nota_fiscal_completo(self, cliente):
        """Testa validação completa de nota fiscal"""
        from notas.services import ValidacaoService
        from notas.models import NotaFiscal
        
        # 1. Criar nota fiscal válida
        nota = NotaFiscal(
            cliente=cliente,
            nota='NF123',
            valor=Decimal('1000.00'),
            peso=100
        )
        
        valido, erros = ValidacaoService.validar_nota_fiscal_antes_salvar(nota)
        assert valido is True
        assert len(erros) == 0
        
        # 2. Testar com valor negativo
        nota.valor = Decimal('-100.00')
        valido_negativo, erros_negativo = ValidacaoService.validar_nota_fiscal_antes_salvar(nota)
        
        assert valido_negativo is False
        assert any('negativo' in erro.lower() for erro in erros_negativo)

