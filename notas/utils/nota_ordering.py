"""
Ordenação de notas fiscais pelo número da nota (campo texto).

`order_by('nota')` ordena lexicograficamente (ex.: "10" antes de "2").
Estas funções priorizam valor numérico quando a nota é só dígitos ou
começa por dígitos.
"""
import re
from typing import Any, Iterable, List

from django.db.models import Case, IntegerField, QuerySet, When


def chave_ordenacao_numero_nota(valor: str) -> tuple:
    s = (valor or '').strip()
    if not s:
        return (3, 0, '')
    if s.isdigit():
        return (0, int(s), '')
    m = re.match(r'^(\d+)', s)
    if m:
        return (0, int(m.group(1)), s.lower())
    return (1, 0, s.lower())


def ordenar_instancias_notas_fiscais(notas: Iterable[Any]) -> List[Any]:
    return sorted(notas, key=lambda nf: chave_ordenacao_numero_nota(nf.nota))


def ordenar_queryset_notas_por_numero(qs: QuerySet) -> QuerySet:
    lista = list(qs)
    if not lista:
        return qs
    lista.sort(key=lambda nf: chave_ordenacao_numero_nota(nf.nota))
    ids = [nf.pk for nf in lista]
    preserved = Case(
        *[When(pk=pk, then=i) for i, pk in enumerate(ids)],
        output_field=IntegerField(),
    )
    model = qs.model
    return model.objects.filter(pk__in=ids).annotate(_ord_nota_num=preserved).order_by('_ord_nota_num')
