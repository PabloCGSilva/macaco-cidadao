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

echo "Iniciando bot..."
exec python run_bot.py
