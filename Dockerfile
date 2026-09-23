FROM python:3.10-slim

# Install system dependencies for OpenCV and PDF
RUN apt-get update && apt-get install -y \
    poppler-utils \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Cache bust: 2026-09-24-v7
RUN pip install --no-cache-dir --force-reinstall -r requirements.txt

# Copy the rest of the app
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]