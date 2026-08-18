# Dockerfile

# Python 3.14 base image
FROM python:3.14-slim

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=inventory.settings
ENV UV_SYSTEM_PYTHON=1

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    redis-tools \
    curl \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Install UV (Fast Python package installer)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}" 

# Copy UV configuration files
COPY pyproject.toml uv.lock ./

# Install dependencies using UV (fast!)
RUN uv pip install --system -r pyproject.toml


RUN uv pip install --system whitenoise

# Copy entire project
COPY . .

RUN mkdir -p /var/log/gunicorn && chmod 755 /var/log/gunicorn

# Collect static files
#RUN uv run python manage.py collectstatic --noinput --clear


RUN uv pip install --system gunicorn


RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /var/log/gunicorn

USER appuser


# ✅ Gunicorn with WhiteNoise (no need for Nginx for static files)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--access-logfile", "/var/log/gunicorn/access.log", "--error-logfile", "/var/log/gunicorn/error.log", "inventory.wsgi:application"]