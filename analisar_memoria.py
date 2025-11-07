#!/usr/bin/env python
"""
Script para analisar o uso de memória do sistema
Execute: python analisar_memoria.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sistema_estelar.settings')
django.setup()

from notas.models import (
    NotaFiscal, Cliente, Motorista, Veiculo, RomaneioViagem,
    HistoricoConsulta, AgendaEntrega, DespesaCarregamento,
    CobrancaCarregamento, Usuario
)

def analisar_uso_memoria():
    """Analisa o uso de memória do sistema"""
    
    print("=" * 60)
    print("  ANÁLISE DE USO DE MEMÓRIA - SISTEMA ESTELAR")
    print("=" * 60)
    print()
    
    # Contar registros
    print("📊 QUANTIDADE DE REGISTROS NO BANCO:")
    print("-" * 60)
    
    modelos = {
        'Notas Fiscais': NotaFiscal,
        'Clientes': Cliente,
        'Motoristas': Motorista,
        'Veículos': Veiculo,
        'Romaneios': RomaneioViagem,
        'Histórico Consultas': HistoricoConsulta,
        'Agenda Entrega': AgendaEntrega,
        'Despesas Carregamento': DespesaCarregamento,
        'Cobranças Carregamento': CobrancaCarregamento,
        'Usuários': Usuario,
    }
    
    total_registros = 0
    for nome, modelo in modelos.items():
        count = modelo.objects.count()
        total_registros += count
        print(f"  {nome:.<30} {count:>10} registros")
    
    print("-" * 60)
    print(f"  {'TOTAL':.<30} {total_registros:>10} registros")
    print()
    
    # Análise de queries problemáticas
    print("🔍 ANÁLISE DE QUERIES POTENCIALMENTE PROBLEMÁTICAS:")
    print("-" * 60)
    
    # Verificar queries que podem carregar muitos dados
    notas_count = NotaFiscal.objects.count()
    if notas_count > 1000:
        print(f"  ⚠️  Notas Fiscais: {notas_count} registros")
        print("     Recomendação: Implementar paginação nas listagens")
    
    romaneios_count = RomaneioViagem.objects.count()
    if romaneios_count > 500:
        print(f"  ⚠️  Romaneios: {romaneios_count} registros")
        print("     Recomendação: Implementar paginação nas listagens")
    
    # Verificar se há queries sem select_related/prefetch_related
    print()
    print("💡 RECOMENDAÇÕES DE OTIMIZAÇÃO:")
    print("-" * 60)
    print("  1. Implementar paginação em todas as listagens")
    print("  2. Usar select_related() para ForeignKey")
    print("  3. Usar prefetch_related() para ManyToMany")
    print("  4. Limitar queries com .only() ou .defer() quando possível")
    print("  5. Usar .iterator() para grandes datasets")
    print("  6. Reduzir workers do Gunicorn se necessário")
    print("  7. Limitar max_requests para reiniciar workers mais frequentemente")
    print()
    
    # Verificar configurações atuais
    print("⚙️  CONFIGURAÇÕES ATUAIS:")
    print("-" * 60)
    
    # Ler gunicorn.conf.py
    try:
        with open('gunicorn.conf.py', 'r') as f:
            content = f.read()
            if 'workers = 2' in content:
                print("  ✓ Gunicorn workers: 2 (adequado para 2GB RAM)")
            if 'max_requests = 500' in content:
                print("  ✓ Max requests: 500 (workers reiniciam a cada 500 requisições)")
            if 'preload_app = False' in content:
                print("  ✓ Preload app: False (economiza memória)")
    except:
        print("  ⚠️  Não foi possível ler gunicorn.conf.py")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    analisar_uso_memoria()

