# News Service - Agro News Microservice 🌾

Django microservice with REST API for automatic parsing, translation, and compression of agricultural news.

## Features

- 🔄 **Automatic RSS Parsing**: Celery tasks parse news from agricultural sites every 6 hours
- 🤖 **AI Processing**: OpenAI GPT-4 translates English articles to Ukrainian and creates concise summaries
- 📊 **REST API**: Full-featured API with filtering, search, and pagination
- 🗄️ **PostgreSQL**: Reliable data storage
- 🚀 **Redis + Celery**: Asynchronous task processing
- 🌐 **CORS Support**: Ready for frontend integration

## Technologies

- **Backend**: Django 5.2.7, Django REST Framework
- **Database**: PostgreSQL 16
- **Task Queue**: Redis 7 + Celery 5.5
- **AI Processing**: OpenAI GPT-4
- **Parsing**: BeautifulSoup4, feedparser
- **Containerization**: Docker Compose

## Quick Start

### Prerequisites
- Docker and Docker Compose (for containerized setup)
- **OR** Existing PostgreSQL and Redis instances
- OpenAI API key

### Installation

#### Option 1: Using Docker (All Services)

1. **Clone the repository**:
```bash
git clone <repo-url>
cd news_service
```

2. **Create .env file**:
```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

3. **Start services**:
```bash
docker-compose up -d
```

4. **Run migrations**:
```bash
docker-compose exec web python manage.py migrate
```

#### Option 2: Using Existing PostgreSQL and Redis

1. **Clone the repository**:
```bash
git clone <repo-url>
cd news_service
```

2. **Create database in your existing PostgreSQL**:
```sql
-- Connect to your PostgreSQL instance
CREATE DATABASE news_service_db;
-- Optional: Create dedicated user
CREATE USER news_service_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE news_service_db TO news_service_user;
```

3. **Create .env file with your database settings**:
```bash
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
DB_NAME=news_service_db
DB_USER=news_service_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
EOF
```

4. **Install dependencies and run locally**:
```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Run migrations
python manage.py migrate

# Start Django server
python manage.py runserver

# In separate terminals, start Celery worker and beat
celery -A news_service worker -l info
celery -A news_service beat -l info
```

#### Option 3: Hybrid (Docker + Existing DB/Redis)

Use Docker for the application but connect to your existing PostgreSQL and Redis:

1. **Follow steps 1-3 from Option 2** (clone repo, create DB, setup .env)

2. **Use the override file to disable bundled services**:
```bash
# The docker-compose.override.yml file is already configured
# It will use your local PostgreSQL and Redis instead of containers

# Start only the Django services
docker-compose up -d
```

3. **Run migrations**:
```bash
docker-compose exec web python manage.py migrate
```

5. **Create superuser** (optional):
```bash
# For Docker setup
docker-compose exec web python manage.py createsuperuser

# For local setup
python manage.py createsuperuser
```

6. **Start news parsing**:
```bash
docker-compose exec web python manage.py parse_feeds
```

## API Endpoints

### Main Endpoints

- `GET /api/articles/` - List all articles
- `GET /api/articles/{id}/` - Specific article
- `POST /api/articles/` - Create new article
- `GET /api/articles/ukrainian/` - Only translated Ukrainian articles
- `GET /api/articles/stats/` - Article statistics
- `POST /api/trigger-parse/` - Manual parsing trigger

### Filter Parameters

- `?language=uk` - Filter by language (uk, en, ru)
- `?status=completed` - Filter by status (pending, processing, completed, failed)
- `?search=grain` - Search in titles and descriptions
- `?ordering=-created_at` - Sorting

### Request Examples

```bash
# Get Ukrainian articles
curl "http://localhost:8888/api/articles/?language=uk"

# Search articles about grain
curl "http://localhost:8888/api/articles/?search=grain"

# Statistics
curl "http://localhost:8888/api/articles/stats/"

# Trigger parsing
curl -X POST "http://localhost:8888/api/trigger-parse/"
```

## Project Structure

```
news_service/
├── news/                   # Django app
│   ├── models.py          # Article model
│   ├── views.py           # API views + serializers  
│   ├── tasks.py           # Celery tasks
│   ├── utils.py           # Parsing utilities
│   ├── admin.py           # Django admin
│   └── management/        # Django commands
├── news_service/          # Main settings
│   ├── settings.py        # Django settings
│   ├── celery.py          # Celery configuration
│   └── urls.py            # URL routing
├── docker-compose.yml     # Docker services
├── Dockerfile            # Django container
└── pyproject.toml        # Poetry dependencies
```

## RSS Sources Configuration

News sources are configured in `news/tasks.py`:

```python
RSS_FEEDS = [
    "https://www.fao.org/news/rss-feed/en/",
    "https://latifundist.com/novosti/feed/",
    "https://www.world-grain.com/rss/",
    "https://www.agriculture.com/rss/",
]
```

## Management Commands

```bash
# View statistics
docker-compose exec web python manage.py show_stats

# Manual RSS parsing
docker-compose exec web python manage.py parse_feeds

# Admin panel
# http://localhost:8888/admin/

# API documentation
# http://localhost:8888/api/
```

## Celery Monitoring

```bash
# View active tasks
docker-compose exec worker celery -A news_service inspect active

# Worker statistics  
docker-compose exec worker celery -A news_service inspect stats

# Worker logs
docker-compose logs worker

# Beat scheduler logs
docker-compose logs beat
```

## Production Configuration

### Environment Variables

```bash
# Django
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=news.graintrade.info,yourdomain.com

# Database - Use your existing PostgreSQL
DB_NAME=news_service_db
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# OpenAI
OPENAI_API_KEY=your-openai-key

# Redis - Use your existing Redis (different DB number to avoid conflicts)
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Database Setup Notes

**Using Existing PostgreSQL:**
- The service will create a new database `news_service_db` on your existing PostgreSQL server
- Uses port 5432 (default PostgreSQL port) - no conflicts with your existing databases
- You can use your existing PostgreSQL user or create a dedicated one

**Using Existing Redis:**
- Uses Redis database number `1` instead of `0` to avoid conflicts with other services
- Redis supports 16 databases (0-15) by default, so this won't interfere with your existing services
- If you need a different Redis DB number, modify the URLs: `redis://localhost:6379/2`, etc.

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name news.graintrade.info;
    
    location / {
        proxy_pass http://localhost:8888;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Development

### Local Development without Docker

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Run PostgreSQL and Redis locally or via Docker
docker run -d -p 5432:5432 -e POSTGRES_DB=newsdb postgres:16
docker run -d -p 6379:6379 redis:7

# Activate virtual environment
poetry shell

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

# In separate terminals start Celery
celery -A news_service worker -l info
celery -A news_service beat -l info
```

### Testing

```bash
# Run tests
docker-compose exec web python manage.py test

# Or locally
poetry run python manage.py test
```

## Troubleshooting

### Parsing Issues
- Check if RSS sources are available
- View logs: `docker-compose logs worker`

### OpenAI Issues
- Check API key balance
- Verify `OPENAI_API_KEY` setting

### Database Issues
- Check connection: `docker-compose logs db`
- Run migrations: `docker-compose exec web python manage.py migrate`

### Set up Database properly:
```
# Connect as postgres superuser (this should work)
sudo -u postgres psql

# Once in psql, run these commands:
CREATE DATABASE news_service_db;
CREATE USER news_service_user WITH PASSWORD 'news_service_password';
GRANT ALL PRIVILEGES ON DATABASE news_service_db TO news_service_user;
ALTER USER news_service_user CREATEDB;

# Connect to the specific database and grant schema permissions
\c news_service_db
GRANT ALL ON SCHEMA public TO news_service_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO news_service_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO news_service_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO news_service_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO news_service_user;

# Exit psql
\q
```

## License

MIT License

## Support

For questions and support, contact the developer.
