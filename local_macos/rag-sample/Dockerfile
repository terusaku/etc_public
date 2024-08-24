# syntax=docker/dockerfile:1.4
# First stage: Build stage
FROM python:3.11-slim as builder

# Install dependencies for Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy the project files
WORKDIR /app
COPY pyproject.toml poetry.lock ./

# Install project dependencies
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
    pip install --no-cache-dir -r requirements.txt

# Second stage: Runtime stage
FROM python:3.11-slim

# Copy only the necessary files from the builder stage
COPY --from=builder /app /app
COPY --from=builder /opt/poetry /opt/poetry

# Set environment variables
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

# Set the working directory
WORKDIR /app

# Install runtime dependencies
RUN poetry install --no-root --only main --no-interaction --no-ansi

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["poetry", "run", "python", "./app.py"]
