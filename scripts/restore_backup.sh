#!/bin/bash
# Uso: ./scripts/restore_backup.sh macaco_cidadao_20260514_030000.sql.gz
FILENAME=$1
if [ -z "$FILENAME" ]; then
  echo "Uso: $0 <arquivo.sql.gz>"
  exit 1
fi
echo "ATENÇÃO: isto vai sobrescrever o banco atual."
read -p "Confirmar? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then exit 0; fi
gunzip -c "/backups/$FILENAME" | psql "$DATABASE_URL"
echo "Restauração concluída."
