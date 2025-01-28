# syntax=docker/dockerfile:1.4
FROM python:3.11.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libmupdf-dev \
    mupdf \
    mupdf-tools \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

ENV POETRY_HOME="/opt/poetry"
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="$POETRY_HOME/bin:$PATH"
COPY . .
# COPY pyproject.toml poetry.lock /app/
RUN poetry install

# Copy requirements first to leverage Docker cache
# COPY requirements.txt .

# Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt


# Create uploads directory
RUN mkdir -p uploads

# Create db directory for Chroma
RUN mkdir -p db

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]


# FROM python:3.11.9-slim as builder

# # Install dependencies for Poetry
# # RUN apt-get update && apt-get install -y --no-install-recommends \
# RUN apt-get update && apt-get install -y \
#     curl \
#     git \
#     build-essential \
#     python3-dev \
#     # pylzma, backports-lzma 
#     liblzma-dev \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# # Install Poetry
# ENV POETRY_HOME="/opt/poetry"
# RUN curl -sSL https://install.python-poetry.org | python3 -
# ENV PATH="$POETRY_HOME/bin:$PATH"

# # Copy the project files
# COPY pyproject.toml poetry.lock /app/

# WORKDIR /app

# # Install project dependencies
# RUN poetry install --no-root --no-dev
# # RUN poetry install --no-root --no-dev --build pylzma backports-lzma
# # RUN poetry export -f requirements.txt --output requirements.txt --without-hashes && \
# #     pip install --no-cache-dir -r requirements.txt

# # Second stage: Runtime stage
# FROM python:3.11.9-slim

# # Copy only the necessary files from the builder stage
# COPY --from=builder /app /app/
# COPY --from=builder /opt/poetry /opt/poetry
# COPY app.py uploads/ /app/

# # Set environment variables
# ENV POETRY_HOME="/opt/poetry"
# ENV PATH="$POETRY_HOME/bin:$PATH"

# WORKDIR /app

# # Install runtime dependencies
# RUN poetry install --no-root --only main --no-interaction --no-ansi

# # Expose the port the app runs on
# EXPOSE 5000

# # Run the application
# CMD ["poetry", "run", "python", "./app.py"]
