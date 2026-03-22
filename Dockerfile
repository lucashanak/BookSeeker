FROM python:3.11-slim

COPY requirements.txt .
RUN pip install -r requirements.txt --quiet

WORKDIR /app
COPY . .

ENTRYPOINT ["/app/entrypoint.sh"]
