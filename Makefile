.PHONY: help install dev-install format lint typecheck test run migrate makemigrations shell clean docker-build docker-up docker-down docker-logs app

help:
	@echo "Available commands:"
	@echo "  install       Install project dependencies"
	@echo "  dev-install   Install development dependencies"
	@echo "  format        Format code with ruff and isort"
	@echo "  lint          Run linting checks"
	@echo "  typecheck     Run type checking with mypy"
	@echo "  test          Run tests"
	@echo "  run           Start development server"
	@echo "  migrate       Run database migrations"
	@echo "  makemigrations Create new migrations"
	@echo "  shell         Start Django shell"
	@echo "  clean         Clean cache and temporary files"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-up     Start services with Docker Compose"
	@echo "  docker-down   Stop Docker services"
	@echo "  docker-logs   View Docker logs"
	@echo "  app           Create new Django app (usage: make app name=myapp)"

install:
	uv sync

dev-install:
	uv sync --group dev

format:
	uv run ruff format .
	uv run isort .

lint:
	uv run ruff check .

typecheck:
	uv run mypy .

test:
	uv run python manage.py test

run:
	uv run python manage.py runserver

migrate:
	uv run python manage.py migrate

makemigrations:
	uv run python manage.py makemigrations

shell:
	uv run python manage.py shell

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

app:
	@if [ -z "$(name)" ]; then echo "Usage: make app name=myapp"; exit 1; fi
	uv run python manage.py startapp $(name)
	@echo "App '$(name)' created! Don't forget to add it to INSTALLED_APPS in settings.py"
