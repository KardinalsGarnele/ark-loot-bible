@echo off
cd /d %~dp0
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python tools\build_database.py
python -m uvicorn ark_loot_bible.main:app --host 127.0.0.1 --port 8000
