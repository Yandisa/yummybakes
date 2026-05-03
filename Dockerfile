FROM python:3.8-slim

WORKDIR /app

# System deps for Pillow (image processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev zlib1g-dev libpng-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn whitenoise

COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Ensure persistent dirs exist (will be replaced by Coolify volume mounts)
RUN mkdir -p /app/data /app/media

EXPOSE 8000

# Run migrations on startup, then serve with gunicorn
CMD python manage.py migrate --noinput && \
    gunicorn yummybakes.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
