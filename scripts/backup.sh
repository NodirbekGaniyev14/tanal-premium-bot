#!/usr/bin/env bash
# Kunlik backup: pg_dump → yopiq Telegram kanaliga.
# Cron: 0 3 * * * /opt/tanal/scripts/backup.sh >> /var/log/tanal-backup.log 2>&1
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

# shellcheck disable=SC1091
set -a; source .env; set +a

# Dump qaysi kanalga boradi: BACKUP_CHAT_ID bo'lmasa admin guruhiga.
CHAT_ID="${BACKUP_CHAT_ID:-$ADMIN_CHAT_ID}"
STAMP="$(date +%F_%H%M)"
OUT="/tmp/tanal_${STAMP}.sql.gz"

docker compose exec -T postgres \
  pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner \
  | gzip -9 > "$OUT"

SIZE="$(du -h "$OUT" | cut -f1)"

curl -sS -f -X POST \
  "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" \
  -F "chat_id=${CHAT_ID}" \
  -F "caption=🗄 Backup ${STAMP} · ${SIZE}" \
  -F "document=@${OUT}" > /dev/null

rm -f "$OUT"
echo "$(date -Is) backup yuborildi (${SIZE})"
