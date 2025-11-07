# Deploy dos Últimos Commits

Este guia explica como fazer deploy apenas dos últimos N commits no servidor.

## Scripts Disponíveis

### 1. `deploy_ultimos_commits.sh` (Recomendado)
Script que aplica apenas os últimos N commits usando cherry-pick.

**Uso:**
```bash
# Deploy dos 2 últimos commits (padrão)
./deploy_ultimos_commits.sh

# Deploy dos últimos 3 commits
./deploy_ultimos_commits.sh 3
```

### 2. `deploy_commits_especificos.sh`
Versão alternativa com mais verificações.

## Como Usar

### No Servidor (via SSH)

1. Conecte-se ao servidor via SSH
2. Navegue até o diretório do projeto:
   ```bash
   cd /var/www/sistema-estelar
   ```

3. Execute o script:
   ```bash
   bash deploy_ultimos_commits.sh 2
   ```

### O que o Script Faz

1. ✅ Faz backup do banco de dados
2. ✅ Identifica os últimos N commits
3. ✅ Salva estado atual do repositório
4. ✅ Atualiza do repositório remoto
5. ✅ Aplica apenas os commits específicos usando cherry-pick
6. ✅ Ativa ambiente virtual
7. ✅ Instala/atualiza dependências
8. ✅ Executa migrações
9. ✅ Coleta arquivos estáticos
10. ✅ Reinicia serviços (Gunicorn, Nginx)
11. ✅ Verifica status dos serviços

## Exemplo: Deploy dos 2 Últimos Commits

```bash
# 1. Conectar ao servidor
ssh usuario@servidor.com

# 2. Ir para o diretório do projeto (caminho real no servidor)
cd /var/www/sistema-estelar

# 3. Executar deploy
bash deploy_ultimos_commits.sh 2
```

## Verificação dos Commits

Antes de fazer o deploy, você pode verificar quais commits serão aplicados:

```bash
# Ver os últimos 2 commits
git log --oneline -2

# Ver detalhes dos commits
git log -2 --format="%h - %an - %ar - %s"
```

## Troubleshooting

### Erro: "Commit não encontrado"
- Verifique se você fez `git push` dos commits para o repositório remoto
- Execute `git fetch origin main` antes do deploy

### Erro: "Conflitos no cherry-pick"
- O script tentará continuar, mas pode ser necessário resolver conflitos manualmente
- Verifique os logs para mais detalhes

### Erro: "Gunicorn não está rodando"
- O script tentará iniciar o Gunicorn automaticamente
- Se falhar, inicie manualmente:
  ```bash
  nohup gunicorn --bind 127.0.0.1:8000 --workers 3 sistema_estelar.wsgi:application > logs/gunicorn.log 2>&1 &
  ```

## Segurança

⚠️ **IMPORTANTE:**
- Sempre faça backup antes do deploy
- Teste em ambiente de desenvolvimento primeiro
- Monitore os logs após o deploy: `tail -f logs/gunicorn.log`

## Commits dos Últimos Deploys

Para verificar quais commits foram aplicados no último deploy:

```bash
git log --oneline -5
```

