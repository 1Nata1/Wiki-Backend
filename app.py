import sqlite3
import os
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, g, redirect
from flask_cors import CORS

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": true}})


# Serve páginas estáticas do frontend
@app.route("/")
def serve_root():
    # Redireciona pra página de login
    return redirect("/login")


@app.route("/login")
@app.route("/Login")
@app.route("/Login/")
def serve_login():
    return app.send_static_file("Login/index.html")


@app.route("/Login/<path:filename>")
def serve_login_files(filename):
    return app.send_static_file(f"Login/{filename}")


@app.route("/Wiki/")
@app.route("/Wiki")
def serve_wiki_root():
    return app.send_static_file("Wiki/index.html")


@app.route("/Wiki/<path:filename>")
def serve_wiki_files(filename):
    return app.send_static_file(f"Wiki/{filename}")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", "wiki.sqlite")

# Garante que o diretório db existe
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db():
    """Retorna a conexão com o banco (uma por requisição)"""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Cria as tabelas se não existirem"""
    db = get_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            token TEXT,
            moderador INTEGER DEFAULT 0,
            criado_em TEXT DEFAULT (datetime('now', '-3 hours'))
        );

        CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            pagina TEXT NOT NULL DEFAULT 'wendy',
            texto TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pendente',
            criado_em TEXT DEFAULT (datetime('now', '-3 hours')),
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    """)
    db.commit()


@app.after_request
def add_no_cache(response):
    # Evitar cache das páginas HTML
    if response.content_type and "text/html" in response.content_type:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.route("/api.js")
def serve_api_config():
    return app.send_static_file("api.js")


@app.route("/style.css")
def serve_login_style():
    return app.send_static_file("Login/style.css")


@app.route("/Style.css")
def serve_wiki_style():
    return app.send_static_file("Wiki/Style.css")


@app.route("/Imagens/<path:filename>")
def serve_wiki_images(filename):
    return app.send_static_file(f"Wiki/Imagens/{filename}")


@app.route("/Login/stardew-valley-2560-x-1440-background-gkvzx4cplgse4ymy.jpg")
def serve_login_bg():
    return app.send_static_file("Login/stardew-valley-2560-x-1440-background-gkvzx4cplgse4ymy.jpg")


# ===================== TOKEN HELPER =====================

def gerar_token(usuario_id, username):
    """Gera um token simples (hash SHA256 com segredo)"""
    raw = f"{usuario_id}:{username}:{secrets.token_hex(16)}"
    return hashlib.sha256(raw.encode()).hexdigest()


def verificar_token(token):
    """Verifica se o token é válido e retorna os dados do usuário"""
    if not token:
        return None
    db = get_db()
    user = db.execute(
        "SELECT id, nome, username, email, moderador FROM usuarios WHERE token = ?",
        (token,)
    ).fetchone()
    return dict(user) if user else None


# ===================== SESSIONS (tokens salvos no banco) =====================

def salvar_token(usuario_id, token):
    db = get_db()
    db.execute("UPDATE usuarios SET token = ? WHERE id = ?", (token, usuario_id))
    db.commit()


def remover_token(usuario_id):
    db = get_db()
    db.execute("UPDATE usuarios SET token = NULL WHERE id = ?", (usuario_id,))
    db.commit()


# ===================== ROTAS =====================

@app.route("/api/seed", methods=["POST"])
def seed_admin():
    """Cria o moderador inicial (Nata) se não existir"""
    import hashlib as hl
    db = get_db()
    existing = db.execute("SELECT id FROM usuarios WHERE username = ?", ("Nata",)).fetchone()
    if existing:
        return jsonify({"message": "Moderador Nata já existe!"})

    password_hash = hl.sha256("admin123".encode()).hexdigest()
    db.execute(
        "INSERT INTO usuarios (nome, username, email, password_hash, moderador) VALUES (?, ?, ?, ?, 1)",
        ("Nata", "Nata", "nata@wiki.com", password_hash)
    )
    db.commit()
    return jsonify({"success": True, "message": "Moderador Nata criado! Senha: admin123"}), 201


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Wiki API funcionando!"})


@app.route("/api/register", methods=["POST"])
def register():
    """Cadastro de novo usuário"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    nome = data.get("nome", "").strip()
    username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    # Validações
    if not nome or not username or not email or not password:
        return jsonify({"error": "Preencha todos os campos!"}), 400

    if len(password) < 4:
        return jsonify({"error": "A senha deve ter pelo menos 4 caracteres!"}), 400

    if len(username) < 3:
        return jsonify({"error": "O usuário deve ter pelo menos 3 caracteres!"}), 400

    db = get_db()

    # Verifica se username já existe
    if db.execute("SELECT id FROM usuarios WHERE username = ?", (username,)).fetchone():
        return jsonify({"error": "Este usuário já existe!"}), 409

    # Verifica se email já existe
    if db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone():
        return jsonify({"error": "Este email já está cadastrado!"}), 409

    # Cria o usuário
    import hashlib as hl
    password_hash = hl.sha256(password.encode()).hexdigest()
    token = gerar_token(0, username)

    cursor = db.execute(
        "INSERT INTO usuarios (nome, username, email, password_hash, token) VALUES (?, ?, ?, ?, ?)",
        (nome, username, email, password_hash, token)
    )
    db.commit()

    return jsonify({
        "success": True,
        "message": "Conta criada com sucesso!",
        "token": token,
        "user": {
            "id": cursor.lastrowid,
            "nome": nome,
            "username": username,
            "email": email,
            "moderador": False
        }
    }), 201


@app.route("/api/login", methods=["POST"])
def login():
    """Login do usuário"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Preencha usuário e senha!"}), 400

    db = get_db()

    # Procura por username ou email
    user = db.execute(
        "SELECT * FROM usuarios WHERE username = ? OR email = ?",
        (username, username.lower())
    ).fetchone()

    if not user:
        return jsonify({"error": "Usuário ou senha incorretos!"}), 401

    import hashlib as hl
    password_hash = hl.sha256(password.encode()).hexdigest()

    if user["password_hash"] != password_hash:
        return jsonify({"error": "Usuário ou senha incorretos!"}), 401

    # Gera novo token
    token = gerar_token(user["id"], user["username"])
    salvar_token(user["id"], token)

    return jsonify({
        "success": True,
        "message": "Login realizado!",
        "token": token,
        "user": {
            "id": user["id"],
            "nome": user["nome"],
            "username": user["username"],
            "email": user["email"],
            "moderador": bool(user["moderador"])
        }
    })


@app.route("/api/user", methods=["GET"])
def get_user():
    """Dados do usuário logado"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.args.get("token", "")

    user = verificar_token(token)
    if not user:
        return jsonify({"error": "Token inválido!"}), 401

    return jsonify({
        "user": {
            "id": user["id"],
            "nome": user["nome"],
            "username": user["username"],
            "email": user["email"],
            "moderador": bool(user["moderador"])
        }
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    """Logout (remove token)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.json.get("token", "") if request.is_json else ""

    user = verificar_token(token)
    if user:
        remover_token(user["id"])

    return jsonify({"success": True, "message": "Deslogado!"})


# ===================== COMENTÁRIOS =====================

@app.route("/api/comentarios", methods=["GET"])
def listar_comentarios():
    """Lista comentários"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.args.get("token", "")

    user = verificar_token(token)
    pagina = request.args.get("pagina", "wendy")

    db = get_db()

    if user and user["moderador"]:
        # Mod vê todos
        comentarios = db.execute(
            """SELECT c.id, c.usuario_id, c.texto, c.status, c.criado_em,
                      u.nome, u.username, u.moderador as autor_mod
               FROM comentarios c
               JOIN usuarios u ON c.usuario_id = u.id
               WHERE c.pagina = ?
               ORDER BY c.criado_em DESC""",
            (pagina,)
        ).fetchall()
    else:
        # Usuário comum vê só aprovados + seus próprios pendentes
        usuario_id = user["id"] if user else -1
        comentarios = db.execute(
            """SELECT c.id, c.usuario_id, c.texto, c.status, c.criado_em,
                      u.nome, u.username, u.moderador as autor_mod
               FROM comentarios c
               JOIN usuarios u ON c.usuario_id = u.id
               WHERE c.pagina = ?
                 AND (c.status = 'aprovado' OR c.usuario_id = ?)
               ORDER BY c.criado_em DESC""",
            (pagina, usuario_id)
        ).fetchall()

    return jsonify({
        "comentarios": [dict(c) for c in comentarios],
        "pode_moderar": bool(user and user["moderador"])
    })


@app.route("/api/comentarios", methods=["POST"])
def criar_comentario():
    """Cria um novo comentário"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.json.get("token", "") if request.is_json else ""

    user = verificar_token(token)
    if not user:
        return jsonify({"error": "Você precisa estar logado para comentar!"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400

    texto = data.get("texto", "").strip()
    pagina = data.get("pagina", "wendy")

    if not texto:
        return jsonify({"error": "Digite um comentário!"}), 400

    if len(texto) > 1000:
        return jsonify({"error": "Comentário muito longo (máx 1000 caracteres)!"}), 400

    db = get_db()

    # Moderadores têm comentários aprovados automaticamente
    status = "aprovado" if user["moderador"] else "pendente"

    cursor = db.execute(
        "INSERT INTO comentarios (usuario_id, pagina, texto, status) VALUES (?, ?, ?, ?)",
        (user["id"], pagina, texto, status)
    )
    db.commit()

    return jsonify({
        "success": True,
        "message": "Comentário enviado!" if status == "aprovado" else "Comentário enviado! Aguarde aprovação.",
        "comentario": {
            "id": cursor.lastrowid,
            "usuario_id": user["id"],
            "texto": texto,
            "status": status,
            "criado_em": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "nome": user["nome"],
            "username": user["username"],
            "autor_mod": user["moderador"]
        }
    }), 201


@app.route("/api/comentarios/<int:comentario_id>/aprovar", methods=["PUT"])
def aprovar_comentario(comentario_id):
    """Aprova um comentário (só moderador)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        data = request.get_json() or {}
        token = data.get("token", "")

    user = verificar_token(token)
    if not user or not user["moderador"]:
        return jsonify({"error": "Só moderadores podem aprovar comentários!"}), 403

    db = get_db()
    db.execute("UPDATE comentarios SET status = 'aprovado' WHERE id = ?", (comentario_id,))
    db.commit()

    return jsonify({"success": True, "message": "Comentário aprovado!"})


@app.route("/api/comentarios/<int:comentario_id>", methods=["DELETE"])
def excluir_comentario(comentario_id):
    """Exclui um comentário (moderador ou dono)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.args.get("token", "")

    user = verificar_token(token)
    if not user:
        return jsonify({"error": "Não autorizado!"}), 401

    db = get_db()
    comentario = db.execute(
        "SELECT * FROM comentarios WHERE id = ?", (comentario_id,)
    ).fetchone()

    if not comentario:
        return jsonify({"error": "Comentário não encontrado!"}), 404

    # Só o dono ou moderador pode excluir
    if comentario["usuario_id"] != user["id"] and not user["moderador"]:
        return jsonify({"error": "Você não pode excluir este comentário!"}), 403

    db.execute("DELETE FROM comentarios WHERE id = ?", (comentario_id,))
    db.commit()

    return jsonify({"success": True, "message": "Comentário excluído!"})


# ===================== MODERADORES =====================

@app.route("/api/moderadores", methods=["GET"])
def listar_moderadores():
    """Lista moderadores (só moderador)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.args.get("token", "")

    user = verificar_token(token)
    if not user or not user["moderador"]:
        return jsonify({"error": "Não autorizado!"}), 403

    db = get_db()
    mods = db.execute(
        "SELECT id, nome, username FROM usuarios WHERE moderador = 1"
    ).fetchall()

    return jsonify({"moderadores": [dict(m) for m in mods]})


@app.route("/api/usuarios", methods=["GET"])
def listar_usuarios():
    """Lista todos os usuários (só moderador)"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        token = request.args.get("token", "")

    user = verificar_token(token)
    if not user or not user["moderador"]:
        return jsonify({"error": "Não autorizado!"}), 403

    db = get_db()
    usuarios = db.execute(
        "SELECT id, nome, username, email, moderador FROM usuarios ORDER BY nome"
    ).fetchall()

    return jsonify({"usuarios": [dict(u) for u in usuarios]})


@app.route("/api/usuarios/<int:usuario_id>/promover", methods=["PUT"])
def promover_moderador(usuario_id):
    """Promove um usuário a moderador"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        data = request.get_json() or {}
        token = data.get("token", "")

    user = verificar_token(token)
    if not user or not user["moderador"]:
        return jsonify({"error": "Não autorizado!"}), 403

    db = get_db()
    db.execute("UPDATE usuarios SET moderador = 1 WHERE id = ?", (usuario_id,))
    db.commit()

    return jsonify({"success": True, "message": "Usuário promovido a moderador!"})


@app.route("/api/usuarios/<int:usuario_id>/rebaixar", methods=["PUT"])
def rebaixar_moderador(usuario_id):
    """Rebaixa um moderador a usuário comum"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        data = request.get_json() or {}
        token = data.get("token", "")

    user = verificar_token(token)
    if not user or not user["moderador"]:
        return jsonify({"error": "Não autorizado!"}), 403

    # Não pode rebaixar a si mesmo
    if user["id"] == usuario_id:
        return jsonify({"error": "Você não pode rebaixar a si mesmo!"}), 400

    db = get_db()
    db.execute("UPDATE usuarios SET moderador = 0 WHERE id = ?", (usuario_id,))
    db.commit()

    return jsonify({"success": True, "message": "Moderador rebaixado a usuário comum!"})


# Inicializa banco na primeira requisição
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
