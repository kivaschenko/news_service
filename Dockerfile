# Stage 1: Build stage
FROM python:3.12-slim AS builder
WORKDIR /news_service

# Set environment variables
ENV DJANGO_DEBUG=False

# Install curl and Poetry
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy only the necessary files for dependency installation
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root

# Copy the rest of the application code
COPY . .

# Collect static files during build (for production)
RUN python manage.py collectstatic --noinput --clear --settings=core.settings || echo "Static files collection failed, will retry at runtime"

# Stage 2: Final stage
FROM python:3.12-slim AS final
WORKDIR /news_service


# Copy the installed dependencies and application code from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /news_service /news_service

# Run database migrations at startup
CMD python manage.py migrate --noinput --settings=core.settings || echo "Database migration failed, will retry at runtime"

CMD [ "python3", "manage.py", "runserver", "0.0.0.0:8000" ]