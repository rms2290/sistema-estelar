# Plano sequencial de melhorias – Sistema Estelar

Documento que descreve as fases de melhoria da estrutura do sistema, em ordem de dependência e impacto. Cada fase tem critérios de conclusão claros.

---

## Fase 0 – Pré-requisitos ✅ CONCLUÍDA

**Objetivo:** Repositório limpo, testes estáveis e plano documentado antes de refatorações.

| # | Tarefa | Status | Critério de conclusão |
|---|--------|--------|------------------------|
| 0.1 | Remover arquivos `.backup` do repositório | ✅ | Nenhum `*.backup` ou `*.backup2` no código; histórico no Git. |
| 0.2 | Garantir que a suíte `notas.tests` está verde | ✅ | `python manage.py test notas.tests` passa (13 testes). |
| 0.3 | Documentar plano em `docs/` com critérios | ✅ | Este arquivo existe e descreve todas as fases. |

**Conclusão Fase 0:** 2026-02-18 — Itens 0.1 (já estava feito), 0.2 e 0.3 concluídos.

---

## Fase 1 – Quebra do monolito de modelos (`notas/models.py`)

**Objetivo:** Dividir ~2162 linhas em módulos por domínio, mantendo compatibilidade de imports.

| # | Tarefa | Critério de conclusão |
|---|--------|------------------------|
| 1.1 | Criar `notas/models/__init__.py` reexportando todos os modelos | `from notas.models import X` funciona em todo o projeto. |
| 1.2 | Criar `notas/models/mixins.py` (UpperCaseMixin, UsuarioManager) | Mixins e managers em arquivo dedicado. |
| 1.3 | Criar `notas/models/usuario.py` (Usuario) | Modelo Usuario isolado. |
| 1.4 | Criar um arquivo por entidade: cliente, nota_fiscal, motorista, veiculo, romaneio | Modelos principais em módulos separados. |
| 1.5 | Criar módulo(s) auxiliares: TabelaSeguro, HistoricoConsulta, CobrancaCarregamento, AuditoriaLog, etc. | Modelos auxiliares organizados. |
| 1.6 | Atualizar `notas/models/__init__.py` com todos os imports | Nenhum import quebrado. |
| 1.7 | Rodar testes e `manage.py check`; ajustar migrações se necessário | Testes verdes; sem novas migrações por causa da movimentação de código. |

**Entregável:** `notas/models.py` removido ou reduzido a reexport; estrutura em `notas/models/` por domínio.

---

## Fase 2 – Quebra do monolito de views do financeiro (`financeiro/views.py`) ✅ CONCLUÍDA

**Objetivo:** Dividir ~2159 linhas em módulos por funcionalidade, sem alterar comportamento.

| # | Tarefa | Status | Critério de conclusão |
|---|--------|--------|------------------------|
| 2.1 | Criar `financeiro/views/__init__.py` reexportando todas as views | ✅ | URLs continuam apontando para `financeiro.views`. |
| 2.2 | Criar `financeiro/views/dashboard_receitas.py` (dashboard, receitas, caixa funcionário, movimento bancário, controle saldo, criar_funcionario_ajax) | ✅ | Views de dashboard e receitas agrupadas. |
| 2.3 | Criar `financeiro/views/acerto_diario.py` (acerto diário, listar, salvar, carregamento/distribuição, valor_estelar) | ✅ | Views de acerto diário agrupadas. |
| 2.4 | Criar `financeiro/views/movimento_caixa.py` (movimento_caixa, gerenciar, CRUD movimento e acumulado) | ✅ | Views de movimento de caixa agrupadas. |
| 2.5 | Criar `financeiro/views/periodo_caixa.py` (iniciar, pesquisar, visualizar, imprimir, fechar/editar/obter/excluir período) | ✅ | Views de período agrupadas. |
| 2.6 | Criar `financeiro/views/fechamento_caixa.py` (fechamento_caixa) | ✅ | View de fechamento isolada. |
| 2.7 | Atualizar `financeiro/views/__init__.py`; manter `financeiro/urls.py` inalterado em imports | ✅ | Todas as URLs do financeiro respondem como antes. |
| 2.8 | Remover ou esvaziar `financeiro/views.py` | ✅ | Código apenas em `financeiro/views/`. |

**Entregável:** Views do financeiro em módulos; comportamento e testes iguais aos atuais.

**Conclusão Fase 2:** 2026-02-18 — Monolito removido; `financeiro/urls.py` inalterado; `manage.py check` e `notas.tests` OK.

---

## Fase 3 – Camada de serviços no financeiro ✅ CONCLUÍDA

**Objetivo:** Extrair lógica de negócio das views para serviços testáveis.

| # | Tarefa | Status | Critério de conclusão |
|---|--------|--------|------------------------|
| 3.1 | Criar `financeiro/services/__init__.py` | ✅ | Pacote de serviços existe. |
| 3.2 | Criar `financeiro/services/acerto_diario_service.py` (regras de salvar acerto e criar movimentos) | ✅ | Lógica de acerto diário em serviço. |
| 3.3 | Criar `financeiro/services/periodo_caixa_service.py` (abrir/fechar período, saldos/totais) | ✅ | Lógica de período em serviço. |
| 3.4 | Criar `financeiro/services/movimento_caixa_service.py` (CRUD movimento e acumulado) | ✅ | Lógica de movimento em serviço. |
| 3.5 | Refatorar views do financeiro para chamar serviços | ✅ | Views finas; lógica nos serviços. |
| 3.6 | Escrever testes unitários para cada serviço | ✅ | `financeiro/tests/test_services.py` com 14 testes. |

**Entregável:** Lógica crítica do fluxo de caixa em serviços; views delegando aos serviços; testes de serviços verdes.

**Conclusão Fase 3:** 2026-02-18 — Serviços criados; views refatoradas; 14 testes em `financeiro.tests.test_services` + 13 em `notas.tests` = 27 OK.

---

## Fase 4 – Padronização de respostas e erros (APIs internas) ✅ CONCLUÍDA

**Objetivo:** Formato único de JSON para sucesso e erro nas chamadas AJAX/API.

| # | Tarefa | Status | Critério de conclusão |
|---|--------|--------|------------------------|
| 4.1 | Definir contrato: sucesso `{ "success": true, "data": {...}, "message": "..." }`; erro `{ "success": false, "code": "...", "message": "...", "details": {...} }` | ✅ | Contrato documentado em `sistema_estelar/api_utils.py`. |
| 4.2 | Criar `sistema_estelar/api_utils.py`: `json_success()`, `json_error()` e decorator `json_exception_handler` | ✅ | Funções reutilizáveis disponíveis. |
| 4.3 | Substituir gradualmente `JsonResponse` nas views de notas e financeiro por essas funções | ✅ | Financeiro completo; notas (ocorrências NF e erros principais) migrados; front-end compatível. |
| 4.4 | (Opcional) Middleware ou decorator para exceções em views JSON | — | Decorator `json_exception_handler` disponível em `api_utils`; uso opcional nas views. |

**Entregável:** Respostas JSON das APIs internas migradas seguem o contrato; front-end continua funcionando.

**Conclusão Fase 4:** 2026-02-18 — Contrato e `api_utils` criados; views do financeiro e principais de notas migradas; 27 testes (notas + financeiro) OK.

---

## Fase 5 – Logging estruturado ✅ CONCLUÍDA

**Objetivo:** Logs consistentes por ambiente e por tipo de evento.

| # | Tarefa | Status | Critério de conclusão |
|---|--------|--------|------------------------|
| 5.1 | Configurar em `settings.py` e `settings_production.py` formato de log (timestamp, nível, logger, mensagem) | ✅ | LOGGING com formatter `{asctime} {levelname} [{name}] {message}`; loggers `notas` e `financeiro` em INFO. |
| 5.2 | Definir convenção: loggers por app (`notas`, `financeiro`), quando usar INFO/WARNING/ERROR | ✅ | Convenção em `docs/LOGGING.md`. |
| 5.3 | Inserir logs em pontos críticos: login, criação/edição/exclusão de entidades, erros em serviços e views JSON | ✅ | Login/logout e rate limit em `auth_views`; período (iniciar/fechar) e movimento de caixa (criar/editar/excluir) em views do financeiro; erros com `logger.error(..., exc_info=True)` onde faltava. |
| 5.4 | Revisar logs já existentes; remover debug desnecessário em produção | ✅ | Todos usam `getLogger(__name__)`; sem `logger.debug` no código da aplicação; produção com root/django em WARNING. |

**Entregável:** Em produção, erros e ações importantes aparecem em log de forma clara e pesquisável.

**Conclusão Fase 5:** 2026-02-18 — LOGGING configurado em ambos os settings; convenção em `docs/LOGGING.md`; logs em login, período e movimento de caixa; revisão concluída.

---

## Fase 6 – API REST (opcional / médio prazo) ✅ CONCLUÍDA

**Objetivo:** API versionada e documentada para integrações.

| # | Tarefa | Status | Critério de conclusão |
|---|--------|--------|------------------------|
| 6.1 | Adicionar Django REST Framework e drf-spectacular ao `requirements.txt`; configurar em `settings.py` | ✅ | DRF e drf-spectacular instalados; REST_FRAMEWORK e SPECTACULAR_SETTINGS configurados; paginação e TokenAuthentication. |
| 6.2 | Criar app `api` e namespace `api/v1/` em `urls.py`; definir autenticação por token | ✅ | Rota base `/api/v1/`; autenticação Token + Session; endpoint `POST /api/v1/token/` para obter token; middleware ajustado para não redirecionar requisições `/api/`. |
| 6.3 | Implementar endpoints REST para recursos prioritários (ex.: clientes) | ✅ | Recurso **Clientes** exposto: `GET /api/v1/clientes/` (listagem com busca e paginação) e `GET /api/v1/clientes/{id}/` (detalhe); ViewSet read-only; testes em `api.tests`. |
| 6.4 | Documentar API (OpenAPI/Swagger) com drf-spectacular | ✅ | Schema em `/api/schema/`; Swagger UI em `/api/schema/swagger-ui/`; ReDoc em `/api/schema/redoc/`; acesso sem autenticação para leitura da documentação. |

**Entregável:** Pelo menos um recurso em `/api/v1/` com documentação e testes.

**Conclusão Fase 6:** 2026-02-18 — DRF e drf-spectacular configurados; app `api` com v1; recurso Clientes (list/retrieve); documentação Swagger/ReDoc; 4 testes em `api.tests`; 31 testes totais OK.

---

## Ordem recomendada de execução

```
Fase 0 (concluída) → Fase 1 → Fase 2 → Fase 4 → Fase 3 → Fase 5 → Fase 6
```

- **Fase 1** e **Fase 2** podem ser feitas em paralelo ou em sequência.
- **Fase 3** depende da Fase 2 (views do financeiro já modularizadas).
- **Fase 4** pode começar após Fases 1 e 2.
- **Fase 6** é opcional e pode ficar para o final.

---

## Resumo por fase

| Fase | Nome | Entregável principal |
|------|------|----------------------|
| 0 | Pré-requisitos | Repo limpo, testes verdes, plano documentado ✅ |
| 1 | Modelos | `notas/models` em módulos por domínio |
| 2 | Views financeiro | `financeiro/views` em módulos por funcionalidade ✅ |
| 3 | Serviços financeiro | Lógica de caixa em serviços + testes ✅ |
| 4 | API responses | Formato único de JSON sucesso/erro ✅ |
| 5 | Logging | Logs estruturados em pontos críticos ✅ |
| 6 | API REST | `/api/v1/` + documentação ✅ |

---

*Última atualização: 2026-02-18. Fases 0, 1, 2, 3, 4, 5 e 6 concluídas.*
