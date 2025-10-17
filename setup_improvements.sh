#!/bin/bash

# Setup script for the improved news service

echo "=== News Service Setup ==="

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

echo "1. Installing required packages..."

# Check if poetry is available
if command -v poetry &> /dev/null; then
    echo "Using Poetry to install packages..."
    poetry add transformers torch sentencepiece lxml newspaper3k langdetect python-dateutil
else
    echo "Poetry not found. Please install packages manually:"
    echo "pip install transformers torch sentencepiece lxml newspaper3k langdetect python-dateutil"
    echo ""
    echo "Or add these to your pyproject.toml and run 'poetry install'"
    echo ""
    read -p "Press Enter to continue with database migration..."
fi

echo ""
echo "2. Creating database migrations..."
python manage.py makemigrations

echo ""
echo "3. Applying migrations..."
python manage.py migrate

echo ""
echo "4. Testing the system..."
if [ -f "test_scraping.py" ]; then
    python test_scraping.py
else
    echo "Test script not found, skipping tests"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Start Celery worker: celery -A news_service worker -l INFO"
echo "2. Start Celery beat: celery -A news_service beat -l INFO"
echo "3. Run article discovery: python manage.py parse_feeds"
echo "4. Check statistics: python manage.py show_stats"
echo ""
echo "For more information, see IMPROVEMENTS.md"