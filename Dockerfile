FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY uv.lock pyproject.toml ./

RUN uv sync --frozen

COPY . .

EXPOSE 8000

CMD ["uv", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
