# DABubble

A Slack-style chat application. Backend: Django REST Framework + PostgreSQL. Frontend: Angular (added later). Runs via Docker.

## Requirements
- Docker & Docker Compose

## Getting started
1. Copy the env template and fill in values:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Start the stack:
   ```bash
   docker compose up --build
   ```
3. The API is available at http://localhost:8000/

## Tests
```bash
docker compose run --rm web pytest
```
