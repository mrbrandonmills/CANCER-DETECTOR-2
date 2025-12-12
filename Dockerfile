FROM python:3.11-slim-bookworm

# Install system dependencies for WeasyPrint
# These are required for Cairo (rendering) and Pango (text layout)
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create templates directory if it doesn't exist
RUN mkdir -p templates

# Default port - Railway will override via ENV if needed
ENV PORT=8000
EXPOSE 8000

# Use ENTRYPOINT with shell form for proper variable expansion
ENTRYPOINT ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port $PORT"]
