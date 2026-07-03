"""Testes de emissão de romaneio."""
import pytest
from django.urls import reverse

from notas.models import RomaneioViagem
from notas.services import RomaneioService
from notas.tests.conftest import RomaneioViagemFactory, NotaFiscalFactory


@pytest.mark.django_db
class TestEmitirRomaneio:
    def _criar_romaneio_salvo(self, cliente, motorista, veiculo, codigo='ROM-TEST-001'):
        romaneio = RomaneioViagemFactory(
            codigo=codigo,
            cliente=cliente,
            motorista=motorista,
            veiculo_principal=veiculo,
            status='Salvo',
        )
        nota = NotaFiscalFactory(cliente=cliente, status='Depósito')
        romaneio.notas_fiscais.add(nota)
        return romaneio, nota

    def test_emitir_romaneio_salvo_atualiza_status_e_notas(self, cliente, motorista, veiculo):
        romaneio, nota = self._criar_romaneio_salvo(cliente, motorista, veiculo)

        romaneio_emitido, sucesso, mensagem = RomaneioService.emitir_romaneio(romaneio)

        assert sucesso is True
        assert 'emitido com sucesso' in mensagem.lower()
        romaneio_emitido.refresh_from_db()
        nota.refresh_from_db()
        assert romaneio_emitido.status == 'Emitido'
        assert nota.status == 'Enviada'

    def test_emitir_romaneio_ja_emitido_falha(self, cliente, motorista, veiculo):
        romaneio, _ = self._criar_romaneio_salvo(cliente, motorista, veiculo)
        romaneio.status = 'Emitido'
        romaneio.save(update_fields=['status'])

        _, sucesso, mensagem = RomaneioService.emitir_romaneio(romaneio)

        assert sucesso is False
        assert 'Salvo' in mensagem

    def test_view_emitir_romaneio_post(self, authenticated_client, cliente, motorista, veiculo):
        romaneio, _ = self._criar_romaneio_salvo(cliente, motorista, veiculo)
        url = reverse('notas:emitir_romaneio', kwargs={'pk': romaneio.pk})

        response = authenticated_client.post(url)

        assert response.status_code == 302
        assert response.url == reverse('notas:detalhes_romaneio', kwargs={'pk': romaneio.pk})
        romaneio.refresh_from_db()
        assert romaneio.status == 'Emitido'

    def test_view_emitir_romaneio_get_redireciona(self, authenticated_client, cliente, motorista, veiculo):
        romaneio, _ = self._criar_romaneio_salvo(cliente, motorista, veiculo)
        url = reverse('notas:emitir_romaneio', kwargs={'pk': romaneio.pk})

        response = authenticated_client.get(url)

        assert response.status_code == 302
        romaneio.refresh_from_db()
        assert romaneio.status == 'Salvo'
