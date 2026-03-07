FROM python:3.13-slim

WORKDIR /app

# Сначала копируем зависимости
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь backend (app + etl)
COPY app ./app
COPY ../etl ./etl    # <-- вот эта строчка добавит ETL в контейнер

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]