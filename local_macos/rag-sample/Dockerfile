# syntax=docker/dockerfile:1.4
# First stage: Build stage
FROM python:3.11.9-slim as builder

# Install dependencies for Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    # pylzma, backports-lzma 
    liblzma-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"

# Copy the project files
COPY pyproject.toml poetry.lock /app/

WORKDIR /app

# Install project dependencies
RUN poetry install --no-root --no-dev
# RUN poetry install --no-root --no-dev --build pylzma backports-lzma
# RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
#     pip install --no-cache-dir -r requirements.txt

# Second stage: Runtime stage
FROM python:3.11.9-slim

# Copy only the necessary files from the builder stage
COPY --from=builder /app /app/
COPY --from=builder /opt/poetry /opt/poetry
COPY app.py uploads/ /app/

# Set environment variables
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"

WORKDIR /app

# Install runtime dependencies
RUN poetry install --no-root --only main --no-interaction --no-ansi

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["poetry", "run", "python", "./app.py"]
