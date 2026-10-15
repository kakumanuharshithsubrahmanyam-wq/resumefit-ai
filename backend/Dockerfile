FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY pytest.ini .
COPY start.sh ./start.sh

RUN mkdir -p /app/data && chmod +x /app/start.sh

ENV DATABASE_URL=sqlite:////app/data/resumefit.db

EXPOSE 8000

CMD ["/app/start.sh"]
