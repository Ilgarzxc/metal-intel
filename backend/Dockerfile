# Базовый образ
FROM python:3.13-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем файл зависимостей и ставим их
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь backend, чтобы были app, etl и migrations
COPY backend/ ./

# Устанавливаем переменную окружения, чтобы Python видел модуль app
ENV PYTHONPATH=/app

# Команда по умолчанию для запуска сервера
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]