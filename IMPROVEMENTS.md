# News Service Improvements

This document describes the major improvements made to the news service system to replace RSS feed parsing with direct news page scraping and open-source summarization.

## Key Changes

### 1. Enhanced Article Extraction (`news/utils.py`)

**New Features:**
- **Multiple extraction methods**: Uses both `newspaper3k` library and BeautifulSoup fallback
- **Link discovery**: Automatically finds article links from news website main pages
- **Better content extraction**: Improved selectors for extracting article content
- **Language detection**: Automatic language detection using `langdetect`
- **Metadata extraction**: Extracts authors, publish dates, meta descriptions, and images
- **URL filtering**: Intelligent filtering to avoid non-article URLs

**New Functions:**
- `extract_links_from_news_site()`: Discovers article links from news sites
- `fetch_article_with_newspaper()`: Primary extraction using newspaper3k
- `fetch_article_with_bs4()`: Fallback extraction using BeautifulSoup
- `extract_title()`, `extract_content()`, `extract_publish_date()`: Specialized extractors

### 2. Open-Source Summarization (`news/summarizer.py`)

**Features:**
- **Hugging Face Transformers**: Uses open-source models like BART for summarization
- **No API costs**: Eliminates dependency on paid OpenAI API
- **GPU support**: Automatically uses GPU if available for faster processing
- **Model fallbacks**: Falls back to smaller models if main model fails
- **Language awareness**: Handles different languages and adds appropriate notes

**Models Used:**
- Primary: `facebook/bart-large-cnn` (high quality)
- Fallback: `sshleifer/distilbart-cnn-12-6` (smaller, faster)

### 3. Improved Data Model (`news/models.py`)

**New Fields:**
- `authors`: Article authors
- `meta_description`: Meta description from source
- `top_image`: URL of main article image
- `source_domain`: Domain of the source website
- **Extended language support**: Added German, French, Spanish, Italian, and "unknown"

### 4. Redesigned Task System (`news/tasks.py`)

**New Task Functions:**
- `discover_and_process_articles()`: Main discovery and processing task
- `process_single_article()`: Process individual articles
- `reprocess_failed_articles()`: Retry failed articles
- `cleanup_old_articles()`: Clean up old failed articles
- `process_specific_url()`: Manual processing of specific URLs

**News Sources:**
Replaced RSS feeds with direct news site scraping:
- agriculture.com
- agweb.com
- farm-online.com.au
- agdaily.com
- farminguk.com
- producer.com
- grainnet.com
- agfax.com

### 5. Enhanced Management Commands

**Updated Commands:**
- `parse_feeds`: Now discovers and processes articles from news sites
  - Added `--url` option to process specific URLs
- `show_stats`: Enhanced statistics with language distribution, domain stats, word counts

## Installation and Setup

### Required Dependencies

Add to `pyproject.toml`:
```toml
transformers = "^4.36.0"
torch = "^2.1.0"
sentencepiece = "^0.1.99"
lxml = "^4.9.3"
newspaper3k = "^0.2.8"
langdetect = "^1.0.9"
python-dateutil = "^2.8.2"
```

### Database Migration

Run the migration to add new fields:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Model Download

The summarization models will be downloaded automatically on first use. For better performance:

1. **GPU Setup** (optional but recommended):
   - Install CUDA-compatible PyTorch
   - Models will automatically use GPU if available

2. **Pre-download models** (optional):
   ```python
   from transformers import pipeline
   
   # This will download the model
   summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
   ```

## Usage

### Basic Usage

1. **Discover and process articles**:
   ```bash
   python manage.py parse_feeds
   ```

2. **Process a specific URL**:
   ```bash
   python manage.py parse_feeds --url "https://example.com/article"
   ```

3. **View statistics**:
   ```bash
   python manage.py show_stats
   ```

### Celery Tasks

In your application:
```python
from news.tasks import discover_and_process_articles, process_single_article

# Discover articles from all news sites
task = discover_and_process_articles.delay()

# Process a specific URL
task = process_single_article.delay("https://example.com/article")
```

### Testing

Run the test script to verify everything works:
```bash
python test_scraping.py
```

## Benefits

### 1. Cost Reduction
- **No API costs**: Eliminates OpenAI API dependency
- **Free models**: Uses open-source Hugging Face models
- **Local processing**: All processing happens locally

### 2. Better Content Discovery
- **Direct scraping**: No dependency on RSS feeds
- **More sources**: Can extract from any news website
- **Fresh content**: Discovers latest articles automatically

### 3. Improved Reliability
- **Fallback methods**: Multiple extraction methods ensure higher success rate
- **Error handling**: Better error handling and retry mechanisms
- **Language support**: Automatic language detection

### 4. Enhanced Data Quality
- **Rich metadata**: Extracts authors, images, descriptions
- **Better content**: More accurate content extraction
- **Source tracking**: Tracks source domains for analysis

## Configuration

### News Sources

To add new news sources, edit `NEWS_SITES` in `news/tasks.py`:
```python
NEWS_SITES = [
    "https://yournewssite.com/news",
    # Add more sites here
]
```

### Summarization Model

To change the summarization model, modify `news/summarizer.py`:
```python
def __init__(self, model_name: str = "your-preferred-model"):
```

Popular alternatives:
- `google/pegasus-cnn_dailymail` (better for news)
- `microsoft/DialoGPT-medium` (for conversational summaries)
- `t5-base` (more general purpose)

### Processing Limits

Adjust processing limits in `news/tasks.py`:
```python
# Number of articles to discover per site
article_links = extract_links_from_news_site(site_url, max_links=10)

# Number of failed articles to retry
failed_articles = Article.objects.filter(status='failed')[:20]
```

## Monitoring and Maintenance

### Regular Tasks

1. **Daily processing**:
   ```bash
   python manage.py parse_feeds
   ```

2. **Weekly cleanup**:
   ```bash
   # This is handled automatically by cleanup_old_articles task
   ```

3. **Retry failed articles**:
   ```bash
   # Set up periodic task for reprocess_failed_articles
   ```

### Monitoring

Use the enhanced statistics command:
```bash
python manage.py show_stats
```

Monitor:
- Success/failure rates
- Language distribution
- Source domain performance
- Average processing times

## Troubleshooting

### Common Issues

1. **Models not downloading**:
   - Check internet connection
   - Verify disk space (models can be 1-2GB)
   - Check Python package installations

2. **Content extraction fails**:
   - Some sites may block scraping
   - Check if site structure changed
   - Verify User-Agent settings

3. **Summarization errors**:
   - Check if text is too long (>1024 tokens)
   - Verify model compatibility
   - Try fallback model

### Performance Optimization

1. **Use GPU**: Install CUDA-compatible PyTorch for faster summarization
2. **Batch processing**: Process multiple articles together
3. **Model caching**: Keep models loaded in memory for repeated use
4. **Content filtering**: Filter out very short or irrelevant content

## Migration from Old System

### Backward Compatibility

The old task names are still available:
- `parse_feeds()` → calls `discover_and_process_articles()`
- `fetch_and_summarize_article()` → calls `process_single_article()`

### Data Migration

Existing articles will continue to work. New fields will be empty but can be populated by reprocessing:
```python
from news.tasks import reprocess_failed_articles
reprocess_failed_articles.delay()
```

## Future Enhancements

Potential improvements:
1. **Translation support**: Add automatic translation to Ukrainian
2. **Better language detection**: More accurate language identification
3. **Image processing**: Download and process article images
4. **Sentiment analysis**: Add sentiment scoring
5. **Topic clustering**: Group related articles
6. **Duplicate detection**: Avoid processing duplicate articles