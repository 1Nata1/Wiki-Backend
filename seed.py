#!/usr/bin/env python3
"""
Script para criar o moderador inicial (Nata) e fazer seed do banco.
Execute após o deploy:
    python seed.py --url https://wiki-backend.onrender.com
"""

import sys
import urllib.request
import json

API_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
API_URL = API_URL.rstrip("/")

def request(path, data=None, method="POST"):
    url = f"{API_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

if __name__ == "__main__":
    print(f"🌱 Seed em: {API_URL}")

    # 1. Health check
    try:
        health = request("/api/health", method="GET")
        print(f"✅ Server OK: {health['message']}")
    except Exception as e:
        print(f"❌ Server não respondeu: {e}")
        sys.exit(1)

    # 2. Criar moderador Nata
    result = request("/api/seed")
    print(f"👤 Moderador: {result.get('message', result.get('error', 'OK'))}")

    # 3. Criar um comentário de exemplo
    # Primeiro faz login
    login = request("/api/login", {"username": "Nata", "password": "admin123"})
    if login.get("success"):
        token = login["token"]
        comment = request("/api/comentarios", {
            "texto": "Bem-vindos à Wiki da Comunidade! 🎉",
            "pagina": "wendy",
            "token": token
        })
        print(f"💬 Comentário: {comment.get('message', 'OK')}")
    else:
        print(f"⚠️  Não foi possível fazer login: {login.get('error')}")

    print("\n✅ Seed completo!")
    print(f"\n📋 Credenciais do moderador:")
    print(f"   Usuário: Nata")
    print(f"   Senha:   admin123")
    print(f"\n⚠️  Mude a senha após o primeiro login!")
