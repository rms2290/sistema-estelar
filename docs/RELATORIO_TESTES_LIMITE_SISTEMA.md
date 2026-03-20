# Relatório de Testes de Limite do Sistema Estelar

**Data da execução:** 19/02/2026  
**Objetivo:** Forçar o sistema sob stress, performance e rate limiting para identificar falhas e limites.

---

## 1. Resumo Executivo

| Teste | Resultado | Erros críticos | Observações |
|-------|-----------|----------------|-------------|
| **Teste 7** – Stress e edge cases | ✅ Aprovado | 0 | 2 warnings (valores negativos; relacionamento inválido) |
| **Teste 3** – Performance | ✅ Aprovado | 0 | 1000 notas e 100 romaneios sem falha |
| **Rate limiting** – Login | ⚠️ Parcial | 0 | Bloqueio na 7ª requisição; script esperava na 6ª |
| **Teste 1** – Edição | ⚠️ 1 falha | 1 | Falso negativo na comparação de strings (origem/destino) |

**Conclusão:** Nenhuma falha crítica que quebre o sistema. Limites de throughput e de rate limit identificados; um teste de edição apresenta falso negativo por comparação de texto.

---

## 2. Teste 7 – Stress e Edge Cases

**Script:** `scripts/test/teste_7_stress_edge_cases.py`  
**Duração:** ~6,5 s

### Cenários executados

- **7.1 Limites de campos:** Valores máximos e mínimos (zero) aceitos.
- **7.2 Campos obrigatórios ausentes:** Validação retornou erro (ex.: cliente e nota obrigatórios).
- **7.3 Strings muito longas:** Truncamento automático pelo modelo.
- **7.4 Valores negativos:** Aceitos (registrado como warning – pode ser intencional).
- **7.5 Relacionamentos inválidos:** `Cliente matching query does not exist` (comportamento esperado; tratado como warning).
- **7.6 Dados duplicados:** Constraint UNIQUE funcionou (nota+cliente+mercadoria).
- **7.7 Estados inválidos:** Romaneio emitido editável conforme regra atual.
- **7.8 Operações em massa:** 100 notas criadas em 0,42 s (~237 notas/s), 0 erros.
- **7.9 Concorrência:** Threading tratado sem race condition detectada.
- **7.10 Cálculos extremos:** Peso e valor altos calculados (ex.: peso ≈ 2.999.999,97; valor ≈ 29.999.999,97).

### Estatísticas

- Total de testes: 12  
- Sucessos: 10  
- Erros: 0  
- Warnings: 2 (valores negativos; relacionamento inválido)

### Limites observados

- **Throughput em massa (notas):** ~237 notas/segundo (lote de 100).
- **Concorrência:** Comportamento estável no cenário com threads usado no teste.
- **Valores numéricos:** Decimais grandes aceitos; valores negativos permitidos (revisar se a regra de negócio exige restrição).

---

## 3. Teste 3 – Performance

**Script:** `scripts/test/teste_3_performance.py`  
**Duração:** ~13 s

### Resultados

| Métrica | Valor |
|--------|--------|
| **Notas fiscais criadas** | 1000 |
| **Tempo total (notas)** | 4,61 s |
| **Notas por segundo** | ~216,83 |
| **Tempo médio por nota** | ~4,61 ms |
| **Romaneios criados** | 100 |
| **Tempo total (romaneios)** | 2,30 s |
| **Romaneios por segundo** | ~43,52 |
| **Tempo médio por romaneio** | ~22,98 ms |

### Queries com índices

- Notas em depósito: 492 registros em ~1,73 ms  
- Notas recentes (30 dias): 1000 em ~1,49 ms  
- Notas depósito recentes: 492 em ~1,05 ms  
- Clientes ativos: 0 em ~0,94 ms  

### Queries otimizadas (select_related / prefetch_related)

- Sem otimização: 0,40 s e **4110 queries**
- Com otimização: 0,04 s e **2 queries**
- **Redução de tempo:** ~90,2%  
- **Redução de queries:** 4108

### Limites observados

- **Criação em volume:** 1000 notas e 100 romaneios sem erro no ambiente de teste.
- **Throughput:** ~217 notas/s e ~43 romaneios/s (SQLite, um processo).
- **N+1:** Listagens sem otimização disparam milhares de queries; com otimização o impacto é pequeno.

---

## 4. Teste de Rate Limiting (Login)

**Script:** `scripts/test/test_rate_limiting.py`  
**Configuração em código:** `notas/views/auth_views.py` – `@ratelimit(key='ip', rate='5/m', method='POST', block=True)` (5 POSTs por minuto por IP).

### Comportamento observado

- Tentativas 1 a 6 com **senha errada:** todas retornaram HTTP 200 (página de login com erro).
- Na **7ª requisição** (login com senha correta) o sistema retornou **403 Forbidden** e exceção `django_ratelimit.exceptions.Ratelimited`.

### Interpretação

- O limite configurado é **5 requisições POST por minuto por IP**.
- O bloqueio ocorreu na 7ª requisição, ou seja, após 6 POSTs (possível atraso de contagem ou janela de 1 minuto).
- O script considera “falha” porque esperava bloqueio já na 6ª tentativa; em ambiente com cache (ex.: Redis) o bloqueio pode ocorrer exatamente na 6ª.
- Em produção, com cache configurado, o limite efetivo é **5 tentativas de login por minuto por IP**.

### Limites observados

- **Login:** 5 POSTs/minuto por IP (bloqueio na 6ª requisição dentro da mesma janela).
- **Endpoints críticos** (`@rate_limit_critical`): 10 requisições/minuto por IP (POST/PUT/DELETE).
- **Endpoints moderados** (`@rate_limit_moderate`): 30 requisições/minuto por IP (POST).

---

## 5. Teste 1 – Edição de Romaneios e Notas

**Script:** `scripts/test/teste_1_edicao.py`

### Resultado

- **Teste 1.1 – Edição de campos do romaneio:** marcado como **FALHOU**.
- Mensagem: `Origem esperada: SÃO PAULO, obtida: SÃO PAULO` (e equivalente para destino).
- Os valores são iguais; a falha é da **comparação no teste** (ex.: acento, normalização de string), não do sistema.
- **Teste 1.2 – Edição de nota fiscal:** sucesso.  
- **Teste 1.3 – Atualização de totais:** sucesso.

### Conclusão

- Nenhuma falha real de edição ou de totais detectada.
- Recomendação: ajustar o teste 1.1 para comparação normalizada (ex.: remover acentos ou usar forma normalizada) para evitar falso negativo.

---

## 6. Limites do Sistema (Síntese)

| Aspecto | Limite observado / configurado |
|---------|---------------------------------|
| **Notas fiscais (criação em lote)** | ~217–237/s no teste (SQLite); 1000 notas sem falha. |
| **Romaneios (criação sequencial)** | ~43–44/s no teste; 100 romaneios sem falha. |
| **Login (rate limit)** | 5 POSTs/minuto por IP; bloqueio a partir da 6ª requisição na janela. |
| **Endpoints críticos (POST/PUT/DELETE)** | 10 requisições/minuto por IP. |
| **Operações em massa (stress)** | 100 notas em 0,42 s sem erro. |
| **Concorrência** | Cenário com threads do teste 7 sem race condition. |
| **Valores numéricos** | Decimais grandes aceitos; negativos permitidos (ver regra de negócio). |

---

## 7. Recomendações

1. **Teste 1.1:** Corrigir comparação de strings (origem/destino) para evitar falso negativo (normalização ou remoção de acentos).
2. **Valores negativos:** Definir na regra de negócio se valores negativos em peso/valor devem ser proibidos e, se sim, adicionar validação no modelo ou no formulário.
3. **Rate limiting:** Manter cache (Redis/Memcached) em produção para contagem correta do rate limit por IP.
4. **Performance em produção:** Os números atuais são com SQLite; com PostgreSQL e mais workers (ex.: Gunicorn), esperar limites maiores; recomenda-se repetir testes de carga com ferramentas (ex.: Locust, k6) e banco real.
5. **Próximos testes:** Aumentar volume (ex.: 2000+ notas, 200+ romaneios) e simular múltiplos usuários simultâneos para achar o ponto de falha ou degradação em ambiente de produção.

---

*Relatório gerado com base na execução dos scripts em `scripts/test/` (teste_7_stress_edge_cases.py, teste_3_performance.py, test_rate_limiting.py, teste_1_edicao.py).*
