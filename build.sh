#!/usr/bin/env bash
# Script de build do Render.
#
# Roda na cada deploy:
#   1. Instala dependências
#   2. Coleta arquivos estáticos
#   3. Aplica migrations
#   4. Garante que os exercícios padrão existem (idempotente)

set -o errexit

pip install --upgrade pip
pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_exercises
