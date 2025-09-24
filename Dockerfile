FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
#ENV PORT=8000

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

COPY uv.lock pyproject.toml ./

RUN uv sync --frozen --no-dev

COPY . .

COPY entrypoint.sh ./
RUN chmod +x entrypoint.sh

EXPOSE $PORT

CMD ["./entrypoint.sh"]
