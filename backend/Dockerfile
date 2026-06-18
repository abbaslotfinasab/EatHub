FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements
COPY requirements.txt /app/

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# copy project
COPY . /app/

# collect static (optional in build)
RUN python manage.py collectstatic --noinput || true

# run gunicorn
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000",  "--workers", "3"]