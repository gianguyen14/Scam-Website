FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
# Normally we'd use uv, pip install for slim image
RUN pip install fastapi uvicorn pydantic

COPY src/ ./src/
COPY data/ ./data/

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
