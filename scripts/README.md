# Scripts do Sistema Estelar

Esta pasta contém scripts organizados por categoria.

## 📁 Estrutura

```
scripts/
├── dev/              # Scripts de desenvolvimento
│   ├── ativar.ps1
│   ├── ativar.bat
│   ├── iniciar_servidor.ps1
│   └── iniciar_servidor.bat
├── create_admin.py   # Script para criar usuário administrador
└── README.md         # Este arquivo
```

## 🚀 Scripts de Desenvolvimento

### `dev/ativar.ps1` e `dev/ativar.bat`
Ativa o ambiente virtual e verifica dependências.

**Uso:**
- PowerShell: `.\scripts\dev\ativar.ps1` ou `.\ativar.ps1` (wrapper na raiz)
- CMD: `scripts\dev\ativar.bat` ou `ativar.bat` (wrapper na raiz)

### `dev/iniciar_servidor.ps1` e `dev/iniciar_servidor.bat`
Ativa o ambiente virtual e inicia o servidor Django automaticamente.

**Uso:**
- PowerShell: `.\scripts\dev\iniciar_servidor.ps1` ou `.\iniciar_servidor.ps1` (wrapper na raiz)
- CMD: `scripts\dev\iniciar_servidor.bat` ou `iniciar_servidor.bat` (wrapper na raiz)

## 📝 Scripts Disponíveis

### `create_admin.py`
Script para criar usuário administrador do sistema.

**Uso:**
```bash
python scripts/create_admin.py
```

## 📝 Notas

- Os scripts na raiz (`ativar.ps1`, `ativar.bat`, etc.) são **wrappers** que chamam os scripts organizados aqui.
- Todos os scripts ajustam automaticamente o diretório de trabalho para a raiz do projeto.
- Para mais informações, consulte `docs/COMO_USAR.txt`.

