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
- Docker and Docker Compose
- OpenAI API key

### Installation

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

5. **Create superuser** (optional):
```bash
docker-compose exec web python manage.py createsuperuser
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

# Database
DATABASE_URL=postgresql://user:pass@host:port/dbname

# OpenAI
OPENAI_API_KEY=your-openai-key

# Redis
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

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

## License

MIT License

## Support

For questions and support, contact the developer.
