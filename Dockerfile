FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir .

# Create data directory for SQLite
RUN mkdir -p /app/data

VOLUME ["/app/data"]

CMD ["python", "-m", "bot.main"]
