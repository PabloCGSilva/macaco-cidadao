#!/bin/bash
set -e

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
FILENAME="macaco_cidadao_${TIMESTAMP}.sql.gz"
RETAIN_DAYS=${BACKUP_RETAIN_DAYS:-7}

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Iniciando backup: $FILENAME"

pg_dump "$DATABASE_URL" | gzip > "$BACKUP_DIR/$FILENAME"

echo "[$(date)] Backup concluído: $(du -sh $BACKUP_DIR/$FILENAME)"

# Remove backups mais antigos que RETAIN_DAYS
find "$BACKUP_DIR" -name "*.sql.gz" \
     -mtime +${RETAIN_DAYS} -delete

echo "[$(date)] Backups retidos (últimos ${RETAIN_DAYS} dias):"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "  nenhum"
