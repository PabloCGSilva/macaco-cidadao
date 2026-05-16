#!/bin/sh
# Executa o backup uma vez ao iniciar e depois a cada 24h.
# Container-friendly: sem daemon de cron, sem privilégios especiais.
set -e

INTERVAL_SECS=${BACKUP_INTERVAL_SECS:-86400}   # padrão: 24h

echo "[$(date)] Backup service iniciado. Intervalo: ${INTERVAL_SECS}s"

while true; do
    /pg_backup.sh || echo "[$(date)] AVISO: backup falhou, tentando novamente no próximo ciclo."
    echo "[$(date)] Próximo backup em ${INTERVAL_SECS}s"
    sleep "$INTERVAL_SECS"
done
