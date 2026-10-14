#!/bin/sh
set -eu
cd -- "$(dirname -- "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  printf '%s\n' 'Python 3.10以上が必要です。'
  exit 2
fi
exec python3 -m cleanroomcheck serve --open-browser
