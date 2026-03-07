FROM python:3.13-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install -r requirements.txt

COPY backend/app ./app
COPY backend/models.py .

COPY etl ./etl

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]