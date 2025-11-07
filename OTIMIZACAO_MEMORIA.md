# Otimização de Memória - Sistema Estelar

## Análise do Problema

O servidor está usando mais de 85% da memória, com picos acima de 95%. Isso pode causar lentidão ou travamento do sistema.

## Problemas Identificados

### 1. Queries sem Paginação
- `NotaFiscal.objects.all()` - carrega TODAS as notas fiscais na memória
- `RomaneioViagem.objects.all()` - carrega TODOS os romaneios na memória
- Cálculo de totais usando `sum()` em listas completas

### 2. Falta de Otimização de Queries
- Algumas queries não usam `select_related()` ou `prefetch_related()`
- Queries podem fazer N+1 queries

### 3. Configurações do Gunicorn
- Atualmente: 2 workers (adequado para 2GB RAM)
- Pode ser reduzido para 1 worker se necessário

## Otimizações Implementadas

### 1. Otimização de Queries
- Adicionar `select_related()` para ForeignKey
- Adicionar `prefetch_related()` para ManyToMany
- Usar `.only()` ou `.defer()` para limitar campos carregados
- Usar `.iterator()` para grandes datasets

### 2. Paginação
- Implementar paginação em todas as listagens
- Limitar a 50-100 registros por página

### 3. Cálculo de Totais
- Usar `aggregate()` do Django em vez de `sum()` em Python
- Calcular totais diretamente no banco de dados

### 4. Configurações do Gunicorn
- Reduzir workers se necessário
- Reduzir max_requests para reiniciar workers mais frequentemente
- Manter preload_app = False

## Comandos para Monitorar Memória

```bash
# Ver uso de memória atual
free -h

# Ver processos Python/Gunicorn
ps aux | grep -E "gunicorn|python" | awk '{print $2, $4, $11}' | sort -k2 -rn

# Monitorar memória em tempo real
watch -n 1 free -h

# Ver uso de memória por processo
ps aux --sort=-%mem | head -20
```

## Recomendações Imediatas

1. **Reduzir workers do Gunicorn para 1** (se o servidor tiver menos de 2GB RAM)
2. **Implementar paginação** em todas as listagens
3. **Otimizar queries** com select_related/prefetch_related
4. **Usar aggregate()** em vez de sum() em Python
5. **Limitar max_requests** para 300-400

## Próximos Passos

1. Executar script de análise: `python analisar_memoria.py`
2. Aplicar otimizações nas views
3. Testar uso de memória após otimizações
4. Monitorar por alguns dias

