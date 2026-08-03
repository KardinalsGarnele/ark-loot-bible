# API quick start

```bash
python tools/build_database.py
python -m pip install -e '.[dev]'
uvicorn ark_loot_bible.main:app --reload
```

Open `http://127.0.0.1:8000` for the web preview or `/docs` for OpenAPI.

## Endpoints

- `GET /health`
- `GET /api/v1/items?q=&limit=&offset=`
- `GET /api/v1/items/{item_id}`
