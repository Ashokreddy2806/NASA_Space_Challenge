#!/usr/bin/env bash
# Export the app data, upload it to Vercel Blob, point the frontend at it, deploy to Vercel.
# One-time setup (see deploy/README.md): vercel login; link frontend/; create the Blob store.
set -euo pipefail
cd "$(dirname "$0")/.."

.venv/bin/python -m backend.api.export_static

set -a; source frontend/.env.local; set +a   # BLOB_READ_WRITE_TOKEN
BASE=""
while IFS= read -r f; do
  rel="${f#deploy/static/}"
  url=$(npx vercel blob put "$f" --access public --pathname "$rel" --force --cache-control-max-age 3600 \
        --rw-token "$BLOB_READ_WRITE_TOKEN" 2>&1 | grep -Eo 'https://[^ ]+\.blob\.vercel-storage\.com/[^ ]+' | head -1)
  echo "$rel -> $url"
  BASE="${url%/$rel}"
done < <(find deploy/static -type f | sort)

echo "window.STATIC_DATA_BASE = \"$BASE\";" > frontend/js/config.js
echo "Blob base: $BASE"
(cd frontend && npx vercel deploy --prod --yes)
