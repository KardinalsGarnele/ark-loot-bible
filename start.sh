#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
python tools/build_database.py
exec uvicorn ark_loot_bible.main:app --host 127.0.0.1 --port 8000
