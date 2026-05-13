# 🐳 Docker & Deployment Guide

---

## 🐳 Docker Setup

### 1. Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create logs directory
RUN mkdir -p logs

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health/', timeout=5)"

# Run application
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
```

### 2. docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Database
  db:
    image: postgres:15-alpine
    container_name: mohager_db
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mohager_network

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: mohager_redis
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - mohager_network

  # Django Web Application
  web:
    build: .
    container_name: mohager_web
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4"
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
      - ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./logs:/app/logs
      - ./media:/app/media
      - ./static:/app/staticfiles
    networks:
      - mohager_network

  # Celery Worker (Background Tasks)
  celery:
    build: .
    container_name: mohager_celery
    command: celery -A config worker -l info
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - mohager_network

  # Celery Beat (Scheduled Tasks)
  celery-beat:
    build: .
    container_name: mohager_celery_beat
    command: celery -A config beat -l info
    environment:
      - DEBUG=False
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@db:5432/${DB_NAME}
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    volumes:
      - ./logs:/app/logs
    networks:
      - mohager_network

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: mohager_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./static:/app/staticfiles:ro
      - ./media:/app/media:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    networks:
      - mohager_network

volumes:
  postgres_data:

networks:
  mohager_network:
    driver: bridge
```

### 3. nginx.conf

```nginx
# nginx.conf
upstream django {
    server web:8000;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 100M;

    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /app/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}

# HTTPS (اختياري)
server {
    listen 443 ssl;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. .dockerignore

```
.git
.gitignore
*.pyc
__pycache__
*.egg-info
dist
build
.env.local
.vscode
.idea
*.sqlite3
node_modules
```

---

## 🚀 Docker Commands

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f web
docker-compose logs -f celery

# Stop
docker-compose down

# Remove volumes
docker-compose down -v

# Database shell
docker-compose exec db psql -U postgres -d mohager_db

# Django shell
docker-compose exec web python manage.py shell

# Create migrations
docker-compose exec web python manage.py makemigrations

# Migrate
docker-compose exec web python manage.py migrate

# Create superuser
docker-compose exec web python manage.py createsuperuser

# Collect static
docker-compose exec web python manage.py collectstatic --noinput
```

---

## 🔄 GitHub Actions CI/CD

### .github/workflows/tests.yml

```yaml
name: Run Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: test_db
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        cache: 'pip'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run migrations
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
      run: |
        python manage.py migrate
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### .github/workflows/deploy.yml

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@master
      with:
        host: ${{ secrets.SERVER_HOST }}
        username: ${{ secrets.SERVER_USER }}
        key: ${{ secrets.SERVER_SSH_KEY }}
        script: |
          cd /app/mohager_store
          
          # Pull latest code
          git pull origin main
          
          # Update Docker images
          docker-compose pull
          docker-compose build
          
          # Run migrations
          docker-compose exec -T web python manage.py migrate
          
          # Restart services
          docker-compose restart web celery nginx
          
          # Health check
          curl -f http://localhost/health/ || exit 1
```

---

## 🌍 Deployment الفعلي (Railway, Heroku, AWS)

### Railway (الأسهل)

```bash
# 1. إنشاء project على https://railway.app
# 2. Connect GitHub repo
# 3. أضف environment variables:

DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=...
ALLOWED_HOSTS=yourdomain.com
DEBUG=False

# 4. Platform automatically deploys
```

### AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)

# 2. SSH into instance
ssh -i key.pem ubuntu@your-ec2-ip

# 3. Install dependencies
sudo apt update
sudo apt install -y docker.io docker-compose git
sudo usermod -aG docker $USER

# 4. Clone repo
git clone https://github.com/yourusername/mohager_store.git
cd mohager_store

# 5. Create .env
nano .env

# 6. Run with docker-compose
docker-compose up -d

# 7. Setup SSL with Let's Encrypt
sudo apt install -y certbot python3-certbot-nginx
sudo certbot certonly --standalone -d yourdomain.com

# 8. Update nginx config with SSL certs
```

### Heroku

```bash
# 1. Login
heroku login

# 2. Create app
heroku create yourapponame

# 3. Add buildpack
heroku buildpacks:add heroku/python

# 4. Set environment
heroku config:set SECRET_KEY=...
heroku config:set DEBUG=False

# 5. Add Postgres
heroku addons:create heroku-postgresql:standard-0

# 6. Add Redis
heroku addons:create heroku-redis:premium-0

# 7. Deploy
git push heroku main

# 8. Migrate
heroku run python manage.py migrate
```

---

## 📊 Monitoring & Logging

### Sentry Integration

```python
# settings.py

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn=config('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
    environment=config('ENVIRONMENT'),
    debug=DEBUG,
)

# Test
def trigger_error(request):
    division_by_zero = 1 / 0
    return JsonResponse({'error': 'error'})

# Add URL
path('sentry-debug/', trigger_error),
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# docker-compose.yml - Add this service

elasticsearch:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
  environment:
    - discovery.type=single-node
    - xpack.security.enabled=false
  ports:
    - "9200:9200"

kibana:
  image: docker.elastic.co/kibana/kibana:8.0.0
  ports:
    - "5601:5601"
  depends_on:
    - elasticsearch
```

---

## ✅ Pre-Deployment Checklist

- [ ] DEBUG = False
- [ ] SECRET_KEY changed
- [ ] ALLOWED_HOSTS configured
- [ ] HTTPS enabled
- [ ] Environment variables secured
- [ ] Database backed up
- [ ] Static files collected
- [ ] Media files configured
- [ ] Logging enabled
- [ ] Error tracking (Sentry)
- [ ] Health checks implemented
- [ ] Rate limiting enabled
- [ ] CORS configured
- [ ] Security headers set
- [ ] SSL certificate valid
- [ ] Backups scheduled
- [ ] Monitoring active
- [ ] Load balancer configured

---

## 🚨 Production Best Practices

### 1. Database Backups

```bash
# Automated backup script
#!/bin/bash

BACKUP_DIR="/backups"
DB_NAME="mohager_db"
DB_USER="postgres"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Backup
docker-compose exec -T db pg_dump -U $DB_USER $DB_NAME > $BACKUP_DIR/backup_$TIMESTAMP.sql

# Keep only last 30 days
find $BACKUP_DIR -type f -name "backup_*.sql" -mtime +30 -delete

# Upload to S3 (optional)
aws s3 cp $BACKUP_DIR/backup_$TIMESTAMP.sql s3://your-bucket/backups/
```

### 2. Health Check Endpoint

```python
# views.py
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError

def health_check(request):
    """Health check endpoint for monitoring"""
    
    try:
        # Check database
        with connections['default'].cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check Redis
        from django.core.cache import cache
        cache.set('health_check', 'ok', timeout=1)
        cache.get('health_check')
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok'
        })
    
    except OperationalError:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'error'
        }, status=500)

# urls.py
path('health/', health_check),
```

### 3. Rate Limiting Middleware

```python
# middleware.py
from django_ratelimit.decorators import ratelimit

RATE_LIMITS = {
    'login': '5/m',      # 5 per minute
    'register': '3/h',   # 3 per hour
    'api': '100/h',      # 100 per hour
}
```

### 4. Scheduled Tasks with Celery

```python
# config/celery.py

from celery import Celery
from celery.schedules import crontab

app = Celery('config')

app.conf.beat_schedule = {
    'daily-report': {
        'task': 'apps.analytics.tasks.generate_daily_report',
        'schedule': crontab(hour=0, minute=0),  # Midnight
    },
    'cleanup-sessions': {
        'task': 'apps.users.tasks.cleanup_expired_sessions',
        'schedule': crontab(hour=2, minute=0),  # 2 AM
    },
    'backup-database': {
        'task': 'apps.common.tasks.backup_database',
        'schedule': crontab(hour=3, minute=0),  # 3 AM
    },
}
```

---

## 🎯 Performance Optimization

### 1. Database Connection Pooling

```python
# settings.py

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        ...
        'CONN_MAX_AGE': 600,
    }
}
```

### 2. Query Optimization

```python
# views.py

# Bad: N+1 queries
for order in Order.objects.all():
    print(order.user.email)  # Query for each

# Good: prefetch_related
for order in Order.objects.prefetch_related('user'):
    print(order.user.email)  # One query
```

### 3. Caching Strategy

```python
# views.py

from django.views.decorators.cache import cache_page

# Cache for 1 hour
@cache_page(60 * 60)
def get_products(request):
    ...
```

---

## 📈 Scaling Strategy

### Horizontal Scaling (Multiple Servers)

```
Load Balancer
    ├─ Web Server 1
    ├─ Web Server 2
    └─ Web Server 3
         ↓
    PostgreSQL (Managed)
    Redis Cluster
```

### Docker Swarm or Kubernetes

```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml mohager

# Kubernetes
kubectl apply -f kubernetes/
```

---

## 🎓 التعلم أكتر

- Docker: https://docs.docker.com/
- Kubernetes: https://kubernetes.io/docs/
- CI/CD: https://github.com/features/actions
- AWS: https://aws.amazon.com/getting-started/
- DevOps: https://www.digitalocean.com/community/tutorials

**أنت الآن جاهز للإنتاج! 🚀**
