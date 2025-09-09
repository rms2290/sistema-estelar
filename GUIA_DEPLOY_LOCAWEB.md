# Guia de Deploy na Locaweb - Sistema Estelar

## Problemas Identificados

1. **Erro de protocolo**: Servidor tentando acessar via HTTPS, mas servidor de desenvolvimento só suporta HTTP
2. **Configuração do nginx**: Comandos malformados e configuração incorreta
3. **Configuração de produção**: Necessário ajustar para ambiente de produção

## Soluções

### 1. Configuração do Nginx

Primeiro, vamos criar um arquivo de configuração correto para o nginx:

```bash
# Criar o arquivo de configuração do nginx
sudo nano /etc/nginx/sites-available/sistema-estelar
```

Conteúdo do arquivo:

```nginx
server {
    listen 80;
    server_name seu-dominio.com.br www.seu-dominio.com.br;
    
    # Configurações de arquivos estáticos
    location /static/ {
        alias /var/www/sistema-estelar/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Configurações de arquivos de mídia
    location /media/ {
        alias /var/www/sistema-estelar/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Configurações da aplicação Django
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # Configurações de segurança
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

### 2. Ativar o Site

```bash
# Criar link simbólico para ativar o site
sudo ln -s /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/

# Remover o site padrão (se existir)
sudo rm /etc/nginx/sites-enabled/default

# Testar a configuração do nginx
sudo nginx -t

# Reiniciar o nginx
sudo systemctl restart nginx
```

### 3. Configuração do Gunicorn

```bash
# Instalar o gunicorn
pip install gunicorn

# Executar o gunicorn com as configurações de produção
gunicorn --config gunicorn.conf.py sistema_estelar.wsgi_production:application
```

### 4. Configuração do Sistema

```bash
# Criar diretório de logs
mkdir -p logs

# Configurar permissões
sudo chown -R www-data:www-data /var/www/sistema-estelar
sudo chmod -R 755 /var/www/sistema-estelar

# Coletar arquivos estáticos
python manage.py collectstatic --settings=sistema_estelar.settings_production

# Executar migrações
python manage.py migrate --settings=sistema_estelar.settings_production
```

### 5. Configuração do Supervisor (Opcional)

Para manter o gunicorn rodando automaticamente:

```bash
# Instalar supervisor
sudo apt install supervisor

# Criar arquivo de configuração
sudo nano /etc/supervisor/conf.d/sistema-estelar.conf
```

Conteúdo do arquivo:

```ini
[program:sistema-estelar]
command=/var/www/sistema-estelar/venv/bin/gunicorn --config gunicorn.conf.py sistema_estelar.wsgi_production:application
directory=/var/www/sistema-estelar
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/sistema-estelar.log
```

```bash
# Recarregar supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start sistema-estelar
```

### 6. Verificação Final

```bash
# Verificar status do nginx
sudo systemctl status nginx

# Verificar status do gunicorn
sudo supervisorctl status sistema-estelar

# Verificar logs
tail -f /var/log/nginx/error.log
tail -f /var/log/supervisor/sistema-estelar.log
```

## Comandos de Teste

```bash
# Testar se o servidor está respondendo
curl http://localhost:8000

# Testar se o nginx está funcionando
curl http://seu-dominio.com.br
```

## Troubleshooting

1. **Erro 502 Bad Gateway**: Verifique se o gunicorn está rodando na porta 8000
2. **Erro 404**: Verifique se os arquivos estáticos foram coletados corretamente
3. **Erro de permissão**: Verifique as permissões dos arquivos e diretórios
4. **Erro de banco**: Verifique se as configurações de banco estão corretas

## Próximos Passos

1. Configure o SSL/HTTPS se necessário
2. Configure o backup automático do banco de dados
3. Configure o monitoramento de logs
4. Configure o backup dos arquivos de mídia