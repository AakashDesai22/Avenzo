# AVENZO — Infrastructure

This directory contains all infrastructure configuration for AVENZO.

## Contents

| Directory | Purpose |
|-----------|---------|
| `docker/` | Docker Compose files for development |
| `deployment/` | Deployment guides and configurations |

## Development Setup

```bash
# Start PostgreSQL for local development
docker compose -f docker/docker-compose.dev.yml up -d postgres

# Start PostgreSQL + Backend together
docker compose -f docker/docker-compose.dev.yml --profile full up -d
```

## Files

| File | Purpose |
|------|---------|
| `docker/docker-compose.dev.yml` | Development services |
| `docker/postgres/init.sql` | DB extension initialization |

## Status

- ✅ Docker Compose (dev) — Created
- ❌ Docker not yet installed on current machine
- ❌ Production deployment — Phase 6

See [deployment/README.md](deployment/README.md) for future deployment plans.
