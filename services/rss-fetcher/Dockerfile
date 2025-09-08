FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for newspaper3k and lxml
RUN apt-get update && apt-get install -y \
    gcc \
    libxml2-dev \
    libxslt1-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data for newspaper3k
RUN python -c "import nltk; nltk.download('punkt')"

COPY fetcher.py .

# Create non-root user
RUN useradd -m -u 1000 fetcher && chown -R fetcher:fetcher /app
USER fetcher

CMD ["python", "fetcher.py"]