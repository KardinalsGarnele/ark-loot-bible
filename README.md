# ARK Loot Bible v0.26.0 — Local Preview Release

This package is a real, locally runnable FastAPI + SQLite web application.

## Fastest start

```bash
docker compose up --build
```

Then open `http://127.0.0.1:8000`.

See [QUICKSTART.md](QUICKSTART.md) for Windows, Linux and macOS instructions.

## Available pages

- `/` — global search
- `/blueprint-finder` — reverse blueprint lookup
- `/loot-matrix` — filterable loot matrix and exports
- `/coverage` — verification coverage
- `/admin` — review console
- `/admin/sources` — source workbench
- `/docs` — OpenAPI documentation

The included records are structural/demo data unless explicitly marked VERIFIED.
