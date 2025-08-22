# Použije oficiální Python runtime jako parent image
FROM python:3.11-slim

# Nastaví pracovní adresář v kontejneru
WORKDIR /app

# Nainstaluje systémové závislosti
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Zkopíruje requirements soubor
COPY requirements_production.txt .

# Nainstaluje Python závislosti
RUN pip install --no-cache-dir -r requirements_production.txt

# Zkopíruje zdrojový kód aplikace
COPY . .

# Vytvoří non-root uživatele
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Vytvoří potřebné adresáře
RUN mkdir -p logs static/uploads

# Exponuje port
EXPOSE 5000

# Definuje environment proměnné
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Spustí aplikaci
CMD ["gunicorn", "--worker-class", "eventlet", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]