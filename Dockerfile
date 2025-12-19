FROM mcr.microsoft.com/playwright/python:v1.57.0-jammy

WORKDIR /app

# Install poetry
RUN pip install poetry

# Copy configuration
COPY pyproject.toml poetry.lock* ./

# Install dependencies (no interaction, no ansi)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy source code
COPY src/ ./src/

# Entrypoint is handled by docker-compose command or default to python
CMD ["python", "src/main.py"]
