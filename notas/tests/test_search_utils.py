"""Testes para utilitários de pesquisa."""
import pytest

from notas.utils.search_utils import tem_filtro_preenchido


class TestTemFiltroPreenchido:
    def test_retorna_false_quando_todos_vazios(self):
        data = {'nome': '', 'status': None, 'cliente': ''}
        assert tem_filtro_preenchido(data, ('nome', 'status', 'cliente')) is False

    def test_retorna_true_com_texto(self):
        data = {'nome': 'JOAO', 'status': ''}
        assert tem_filtro_preenchido(data, ('nome', 'status')) is True

    def test_retorna_true_com_valor_nao_string(self):
        data = {'cliente': object()}
        assert tem_filtro_preenchido(data, ('cliente',)) is True

    def test_ignora_campos_ausentes(self):
        data = {'nome': 'TESTE'}
        assert tem_filtro_preenchido(data, ('nome', 'cpf')) is True
