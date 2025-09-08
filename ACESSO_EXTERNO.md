# Acesso Externo ao Sistema Estelar

## Configuração Atual

O sistema está configurado para aceitar conexões externas com as seguintes configurações:

- **IP do Servidor**: 192.168.15.22
- **Porta**: 8000
- **URL de Acesso**: http://192.168.15.22:8000

## Como Acessar de Outros Computadores

### 1. Verificar Conectividade
Primeiro, teste se o computador consegue acessar o servidor:
```bash
ping 192.168.15.22
```

### 2. Acessar o Sistema
Abra um navegador web e digite:
```
http://192.168.15.22:8000
```

### 3. Fazer Login
Use uma das seguintes credenciais:

#### Administrador
- **Usuário**: admin
- **Senha**: 123456

#### Funcionário
- **Usuário**: Celso
- **Senha**: 123456

#### Cliente
- **Usuário**: cliente
- **Senha**: 123456

## Solução de Problemas

### Se não conseguir acessar:

1. **Verificar Firewall**: Certifique-se de que o Windows Firewall permite conexões na porta 8000
2. **Verificar Rede**: Confirme que ambos os computadores estão na mesma rede
3. **Testar Porta**: Use o comando `telnet 192.168.15.22 8000` para testar se a porta está acessível

### Para permitir conexões no Firewall:
```powershell
netsh advfirewall firewall add rule name="Django Sistema Estelar" dir=in action=allow protocol=TCP localport=8000
```

## Comandos Úteis

### Parar o servidor:
```
Ctrl + C
```

### Reiniciar o servidor:
```bash
python manage.py runserver 0.0.0.0:8000
```

### Verificar se o servidor está rodando:
```bash
netstat -an | findstr :8000
```

## Segurança

⚠️ **ATENÇÃO**: Esta configuração permite acesso de qualquer IP na rede. Para produção, configure adequadamente o `ALLOWED_HOSTS` no `settings.py`.

### Para produção, altere em `sistema_estelar/settings.py`:
```python
ALLOWED_HOSTS = ['192.168.15.22', 'localhost', '127.0.0.1']
``` 