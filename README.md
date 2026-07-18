# 🏠 Wiki Backend

Backend completo para a Wiki da Comunidade (WendyJr_).

## 🚀 Como usar

### Rodar localmente

```bash
cd wiki-backend
source .venv/bin/activate  # ou: uv venv && uv pip install -r requirements.txt
python app.py
```

Acesse:
- **Frontend**: http://localhost:8000
- **API Health**: http://localhost:8000/api/health
- **Seed (criar moderador)**: `curl -X POST http://localhost:8000/api/seed`

### Deploy no Render.com

1. Crie conta em https://render.com
2. New → Web Service → conecte o repositório
3. Config:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:${PORT:-10000} app:app`
   - **Plano**: Free

4. Após deploy, rode o seed:
   ```bash
   python seed.py --url https://seu-app.onrender.com
   ```

## 📋 Credenciais

| Usuário | Senha | Tipo |
|---------|-------|------|
| Nata | admin123 | 🔰 Moderador (mude após login!) |

## 🗄️ API Endpoints

### Autenticação
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/register` | Cadastrar usuário |
| `POST` | `/api/login` | Login (retorna token) |
| `GET` | `/api/user?token=...` | Dados do usuário logado |
| `POST` | `/api/logout` | Logout |

### Comentários
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/comentarios?pagina=wendy` | Listar comentários |
| `POST` | `/api/comentarios` | Criar comentário |
| `PUT` | `/api/comentarios/:id/aprovar` | Aprovar (mod) |
| `DELETE` | `/api/comentarios/:id` | Excluir |

### Admin
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/seed` | Criar moderador Nata |
| `GET` | `/api/moderadores` | Listar moderadores |

## 📁 Estrutura

```
wiki-backend/
├── app.py              # Backend Flask
├── seed.py             # Script de seed
├── requirements.txt    # Dependências
├── db/
│   └── wiki.sqlite     # Banco (criado autom.)
├── frontend/
│   ├── api.js          # Helpers JS da API
│   ├── Login/
│   │   ├── index.html  # Tela de login
│   │   ├── cadastro.html
│   │   └── style.css
│   └── Wiki/
│       ├── index.html  # Home da Wiki
│       ├── wendy.html  # Página da streamer
│       ├── perfil.html # Perfil do usuário
│       ├── Style.css
│       └── Imagens/    # Imagens
└── README.md
```
