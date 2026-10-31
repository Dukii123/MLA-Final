#!/usr/bin/env bash
# Chạy demo MLA Nhóm 05 trên máy này. Ctrl+C để dừng.
set -e
cd "$(dirname "$0")"

if [ ! -x .venv/bin/python ]; then
  echo "Chưa có môi trường Python (.venv). Chạy trước:"
  echo "  python3 -m venv .venv"
  echo "  .venv/bin/pip install -r requirements.txt"
  exit 1
fi

PORT="${PORT:-8000}"
URL="http://127.0.0.1:${PORT}"
echo "MLA Nhóm 05 — mở ${URL}"
echo "Lần đầu nạp wav2vec có thể mất 30–60 giây. Ctrl+C để dừng."
if [ "${NO_OPEN:-0}" != "1" ]; then
  ( sleep 2; if command -v open >/dev/null 2>&1; then open "$URL"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"; fi ) >/dev/null 2>&1 &
fi
exec .venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port "$PORT"
