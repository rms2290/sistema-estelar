# Convenção de logging – Sistema Estelar

Documento da Fase 5 do plano de melhorias. Define como e onde registrar logs nas aplicações `notas` e `financeiro`.

---

## Formato dos logs

- **Desenvolvimento e produção:** `{asctime} {levelname} [{name}] {message}`
- Exemplo: `2026-02-18 14:30:00,123 INFO [notas.views.auth_views] Login realizado: usuario=admin`

Opcional (futuro): incluir `request_id` ou `user_id` via filtro no handler para rastreio de requisições.

---

## Loggers por app

| Logger     | Uso |
|-----------|-----|
| `notas`   | Tudo que pertence ao app `notas`: views (auth, clientes, notas fiscais, romaneios, etc.), serviços e utils. Use `logging.getLogger(__name__)` nos módulos; o nome do logger será `notas.views.xxx`, `notas.models.xxx`, etc. |
| `financeiro` | Tudo que pertence ao app `financeiro`: views (caixa, período, acerto, movimento), serviços. Use `logging.getLogger(__name__)` nos módulos. |

Não é necessário configurar loggers por submódulo; os loggers `notas` e `financeiro` já recebem todos os filhos (`notas.views.*`, `financeiro.services.*`, etc.).

---

## Níveis (quando usar)

| Nível   | Quando usar | Exemplos |
|--------|-------------|----------|
| **INFO**  | Ações importantes e conclusões bem-sucedidas | Login com sucesso, logout, criação/edição/exclusão de entidade (resumo), abertura/fechamento de período de caixa, criação de movimento. |
| **WARNING** | Situações anormais mas tratadas; falhas de validação de negócio | Login inválido (credenciais erradas), rate limit, tentativa de operação não permitida (ex.: editar período já fechado). |
| **ERROR**   | Exceções e falhas que exigem atenção | Exceção em view ou serviço, falha ao salvar, erro de integração. Usar `logger.error(..., exc_info=True)` em blocos `except` quando relevante. |
| **DEBUG**   | Evitar em produção; só para desenvolvimento | Não configurado em `settings_production`; em dev pode ser usado temporariamente. |

Regra prática: **INFO** para “o que aconteceu de importante”; **WARNING** para “algo deu errado mas o sistema reagiu”; **ERROR** para “precisamos olhar isso”.

---

## Pontos críticos já cobertos

- **Login/logout:** `notas.views.auth_views` — INFO sucesso, WARNING falha.
- **Views JSON (notas e financeiro):** erros já registrados com `logger.error(..., exc_info=True)`.
- **Serviços:** erros propagados às views, que registram; em serviços pode-se adicionar `logger.warning` ou `logger.error` em regras de negócio que falham (ex.: período já fechado).

---

## Configuração

- **settings.py:** handlers `file` + `console`; loggers `notas` e `financeiro` em INFO; root em INFO.
- **settings_production.py:** apenas handler `file`; loggers `notas` e `financeiro` em INFO; `django` em WARNING; root em WARNING (evita ruído de libs em produção).

Arquivo de log: `logs/django.log` (diretório criado automaticamente em desenvolvimento).

---

## Revisão dos logs existentes (Fase 5.4)

- Todos os módulos de `notas` e `financeiro` usam `logging.getLogger(__name__)`, resultando em loggers `notas.views.*`, `financeiro.views.*`, etc., já cobertos pelos loggers `notas` e `financeiro` na configuração.
- Não há uso de `logger.debug()` no código da aplicação (apenas em scripts de teste), evitando ruído em produção.
- Os pontos que já registravam `logger.error(..., exc_info=True)` em blocos `except` foram mantidos; onde faltava, foi adicionado log de erro e, quando relevante, INFO de sucesso (login, período, movimento de caixa).
