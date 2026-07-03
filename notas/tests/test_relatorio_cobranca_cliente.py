"""Testes do relatório provisório de cobrança ao cliente."""
import pytest
from django.urls import reverse

from notas.models import CobrancaCarregamento
from notas.tests.conftest import RomaneioViagemFactory, NotaFiscalFactory


@pytest.mark.django_db
class TestRelatorioCobrancaCliente:
    def _criar_romaneio_emitido(self, cliente, motorista, veiculo, codigo='ROM-COB-001'):
        romaneio = RomaneioViagemFactory(
            codigo=codigo,
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=veiculo,
            status='Emitido',
        )
        nota = NotaFiscalFactory(cliente=cliente, status='Depósito')
        romaneio.notas_fiscais.add(nota)
        return romaneio

    def test_get_formulario(self, authenticated_client):
        response = authenticated_client.get(reverse('financeiro_v2:relatorio_cobranca_cliente'))
        assert response.status_code == 200
        assert b'Relat\xc3\xb3rio de Cobran\xc3\xa7a' in response.content

    def test_gerar_relatorio_sem_salvar(self, authenticated_client, cliente, motorista, veiculo):
        romaneio = self._criar_romaneio_emitido(cliente, motorista, veiculo)
        antes = CobrancaCarregamento.objects.count()

        response = authenticated_client.post(
            reverse('financeiro_v2:relatorio_cobranca_cliente'),
            {
                'acao': 'gerar_relatorio',
                'cliente': cliente.pk,
                'romaneios': [romaneio.pk],
                'valor_carregamento': '150.00',
                'valor_cte_manifesto': '50.00',
                'observacoes': 'Teste provisório',
            },
        )

        assert response.status_code == 200
        assert b'Teste provis\xc3\xb3rio' in response.content
        assert motorista.nome.encode() in response.content
        assert veiculo.placa.encode() in response.content
        assert romaneio.codigo.encode() in response.content
        assert CobrancaCarregamento.objects.count() == antes

    def test_gerar_relatorio_sem_observacoes_oculta_secao(self, authenticated_client, cliente, motorista, veiculo):
        romaneio = self._criar_romaneio_emitido(cliente, motorista, veiculo)

        response = authenticated_client.post(
            reverse('financeiro_v2:relatorio_cobranca_cliente'),
            {
                'acao': 'gerar_relatorio',
                'cliente': cliente.pk,
                'romaneios': [romaneio.pk],
                'valor_carregamento': '150.00',
                'valor_cte_manifesto': '50.00',
                'observacoes': '',
            },
        )

        assert response.status_code == 200
        assert b'OBSERVACOES POR COBRANCA' not in response.content
        assert b'<th>MOTORISTA</th>' in response.content
        assert b'<th>PLACA</th>' in response.content
        assert b'<th>STATUS</th>' not in response.content

    def test_api_romaneios_para_relatorio(self, authenticated_client, cliente, motorista, veiculo):
        romaneio = self._criar_romaneio_emitido(cliente, motorista, veiculo)
        url = reverse('notas:carregar_romaneios_cliente', kwargs={'cliente_id': cliente.pk})

        response = authenticated_client.get(url, {'para_relatorio': '1'})

        assert response.status_code == 200
        payload = response.json()
        assert payload['success'] is True
        ids = [item['id'] for item in payload['romaneios']]
        assert romaneio.pk in ids
