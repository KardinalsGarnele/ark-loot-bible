FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
COPY . /app
RUN pip install --no-cache-dir .
EXPOSE 8000
CMD ["sh", "-c", "python tools/build_database.py && uvicorn ark_loot_bible.main:app --host 0.0.0.0 --port 8000"]
