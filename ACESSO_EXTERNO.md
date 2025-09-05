# Resolução do Problema de Acesso Externo

## Problema Atual
Você está enfrentando o erro: "You're accessing the development server over HTTPS, but it only supports HTTP."

## Solução Imediata

### 1. Parar o servidor de desenvolvimento atual
```bash
# Pressione Ctrl+C para parar o servidor atual
# Ou se estiver rodando em background:
pkill -f "python manage.py runserver"
```

### 2. Configurar o nginx corretamente
```bash
# Criar arquivo de configuração do nginx
sudo nano /etc/nginx/sites-available/sistema-estelar
```

Cole o seguinte conteúdo:
```nginx
server {
    listen 80;
    server_name _;
    
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

### 3. Ativar o site no nginx
```bash
# Criar link simbólico
sudo ln -s /etc/nginx/sites-available/sistema-estelar /etc/nginx/sites-enabled/

# Remover site padrão
sudo rm /etc/nginx/sites-enabled/default

# Testar configuração
sudo nginx -t

# Reiniciar nginx
sudo systemctl restart nginx
```

### 4. Instalar e configurar o gunicorn
```bash
# Instalar gunicorn
pip install gunicorn

# Executar com configurações de produção
gunicorn --config gunicorn.conf.py sistema_estelar.wsgi_production:application
```

### 5. Configurar permissões
```bash
# Configurar permissões
sudo chown -R www-data:www-data /var/www/sistema-estelar
sudo chmod -R 755 /var/www/sistema-estelar

# Coletar arquivos estáticos
python manage.py collectstatic --noinput --settings=sistema_estelar.settings_production

# Executar migrações
python manage.py migrate --settings=sistema_estelar.settings_production
```

### 6. Testar a aplicação
```bash
# Testar localmente
curl http://localhost:8000

# Testar via nginx
curl http://localhost
```

## Comandos de Verificação

```bash
# Verificar status do nginx
sudo systemctl status nginx

# Verificar logs do nginx
sudo tail -f /var/log/nginx/error.log

# Verificar se o gunicorn está rodando
ps aux | grep gunicorn

# Verificar portas em uso
netstat -tlnp | grep :8000
```

## Troubleshooting

### Se o nginx não iniciar:
```bash
# Verificar configuração
sudo nginx -t

# Verificar logs
sudo journalctl -u nginx
```

### Se o gunicorn não iniciar:
```bash
# Verificar se as dependências estão instaladas
pip list | grep gunicorn

# Executar em modo debug
gunicorn --config gunicorn.conf.py --log-level debug sistema_estelar.wsgi_production:application
```

### Se houver erro 502 Bad Gateway:
```bash
# Verificar se o gunicorn está rodando na porta 8000
netstat -tlnp | grep :8000

# Verificar logs do nginx
sudo tail -f /var/log/nginx/error.log
```

## Próximos Passos

1. **Configurar SSL/HTTPS** (opcional)
2. **Configurar backup automático**
3. **Configurar monitoramento de logs**
4. **Otimizar performance**

## Arquivos Importantes

- `nginx.conf` - Configuração do nginx
- `gunicorn.conf.py` - Configuração do gunicorn
- `sistema_estelar/settings_production.py` - Configurações de produção
- `requirements_production.txt` - Dependências de produção