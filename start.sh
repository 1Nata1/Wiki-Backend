#!/bin/bash
set -e

echo "=== Starting Wiki Backend ==="
echo "Python version: $(python3 --version)"
echo "Current dir: $(pwd)"

# Instalar dependências
echo "=== Installing dependencies ==="
pip3 install -q flask flask-cors gunicorn

echo "=== Starting gunicorn ==="
gunicorn -w 4 -b 0.0.0.0:${PORT:-8000} --timeout 120 app:app
