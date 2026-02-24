# Deployment Guide

## Build Image
```bash
docker build -t sayings-app .
```

## Run Container
```bash
docker run -p 8080:8080 -v $(pwd)/data:/app/data sayings-app
```

## Run with Docker Compose
```bash
docker compose up --build
```

## Access
- Web UI: http://localhost:8080
- API docs: http://localhost:8080/docs

## Environment
Set API keys for a real image provider as environment variables when you swap in a production image generator implementation.
