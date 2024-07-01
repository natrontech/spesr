# Use an NVIDIA CUDA base image with Python 3.12 support
FROM nvidia/cuda:12.5.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install necessary system dependencies and Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-dev \
    build-essential \
    curl \
    git \
    tesseract-ocr \
    tesseract-ocr-deu \
    libtesseract-dev \
    libheif-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Install Python dependencies separately to optimize layer caching and memory usage
RUN pip3 install --upgrade pip && pip3 install --no-cache-dir -r requirements.txt

# Clean up unnecessary files and caches
RUN apt-get purge -y build-essential git \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Expose the port
EXPOSE 8501

# Define healthcheck
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Entry point for the container
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
