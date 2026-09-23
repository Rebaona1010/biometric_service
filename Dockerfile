# Use Alpine Linux - lighter and fewer OpenCV conflicts
FROM python:3.10-alpine

# Install system dependencies for OpenCV, PDF, and compilation
RUN apk add --no-cache \
    poppler-utils \
    build-base \
    cmake \
    libjpeg-turbo-dev \
    libpng-dev \
    tiff-dev \
    libwebp-dev \
    openblas-dev \
    linux-headers \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/cache/apk/*

WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies WITHOUT cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]