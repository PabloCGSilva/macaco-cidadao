#!/bin/bash
set -e

echo "Aguardando PostgreSQL..."
until python -c "
import psycopg2, os
psycopg2.connect(os.environ['DATABASE_URL'])
" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL pronto."

echo "Rodando migrations..."
alembic upgrade head

echo "Populando vereadores..."
if [ -f data/vereadores_bh_tse2024.json ]; then
  python scripts/seed_vereadores.py data/vereadores_bh_tse2024.json
fi

echo "Iniciando painel..."
exec python run_panel.py
