# Guia Seguro para Uso de Dados de Producao no Ambiente Local

Este guia explica como trabalhar com uma copia do banco de producao para analise e otimizacao sem expor dados sensiveis.

## 1) Regras obrigatorias de seguranca

- Nao subir arquivos de banco no GitHub.
- Nao enviar dump por chat, email ou armazenamento publico sem criptografia.
- Nao usar credenciais de producao no ambiente local.
- Nao usar SMTP real, webhooks reais ou integracoes externas reais ao testar localmente.

## 2) Onde guardar o dump no projeto

Use uma pasta local ignorada pelo Git, por exemplo:

- `backups/`

Este repositorio ja ignora:

- `backups/`
- `local_backups/`
- `*.dump`
- `*.sql`
- `*.sql.gz`

## 3) Restaurar dump em banco local separado

Exemplo com PostgreSQL local (recomendado):

1. Criar banco local de trabalho:

```bash
createdb -h localhost -p 5432 -U postgres sistema_estelar_local
```

2. Restaurar dump:

```bash
pg_restore -h localhost -p 5432 -U postgres -d sistema_estelar_local --clean --if-exists "backups/sistema_estelar_YYYY-MM-DD_HHMM.dump"
```

3. Apontar o `.env` local para esse banco:

- `DB_NAME=sistema_estelar_local`
- `DB_HOST=localhost`
- `DB_PORT=5432`
- usuario/senha locais (nao de producao)

## 4) Sanitizacao minima recomendada

Antes de usar dados reais para desenvolvimento, anonimizar campos pessoais:

- nomes de usuarios/clientes
- emails
- telefones
- documentos (CPF/CNPJ/RG)
- enderecos

Se necessario, criar um script/management command para anonimizar automaticamente apos restore.

## 5) Cuidados para nao afetar clientes reais

- Mantenha `DEBUG=True` apenas no local.
- Desative envio de email real no local.
- Nunca use URL/API de producao em testes locais.
- Nunca aponte o ambiente local para o banco remoto de producao.

## 6) Verificacao rapida antes de comitar

Rodar sempre:

```bash
git status
```

Se aparecer arquivo `.dump`/`.sql`, remover do stage:

```bash
git restore --staged <arquivo>
```

## 7) Backup local criptografado (opcional)

Para armazenar dump com mais seguranca:

```bash
gpg --symmetric --cipher-algo AES256 "backups/sistema_estelar_YYYY-MM-DD_HHMM.dump"
```

Isso gera um arquivo `.gpg` criptografado.
