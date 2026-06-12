FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=data/goldforecaster.db

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY src ./src

RUN mkdir -p data

EXPOSE 8000

CMD ["python", "main.py", "--serve"]
