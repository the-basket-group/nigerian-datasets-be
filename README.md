# Nigerian Datasets Backend

Backend API for the Nigerian Datasets project.

## Quick Start

```bash
# See available commands
make help

# Install dependencies
make install

# Copy environment file and configure
cp .env.example .env
# Edit .env with your actual values

# Install a new package
uv add <package-name>

# Create a new Django app
make app name=myapp
```

### Option 1: Run with Docker (PostgreSQL)
```bash
# Start services (PostgreSQL + Django)
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

### Option 2: Run locally (SQLite)
```bash
# Run migrations
make migrate

# Start development server
make run
```

### Option 3: Run locally with PostgreSQL
```bash
# Set environment variable and run
USE_POSTGRES=true make run
```

## Development

```bash
# Format code
make format

# Run linting
make lint

# Run type checking
make typecheck
```

## API Documentation

Visit `http://localhost:8000` to access the Swagger UI documentation.
