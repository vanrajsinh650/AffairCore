# ==================================================
# IndiaBix Scraper - Dockerfile (Production)
# ==================================================
# Build:  docker build -t indiabix-scraper .
# Run:    docker run --rm -v $(pwd)/output:/app/output indiabix-scraper

# Use official slim Python image (smaller = faster, less attack surface)
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install system-level libraries that weasyprint needs for PDF generation
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi-dev \
    shared-mime-info \
    fonts-dejavu-core \
    fonts-gujarati \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements FIRST — Docker caches this layer.
# If requirements.txt doesn't change, pip install is skipped on rebuild.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application source files
COPY . .

# Create output directory — will be mounted as a volume at runtime
RUN mkdir -p /app/output

# Run as non-root user for security (best practice in production)
RUN useradd -m scraper && chown -R scraper:scraper /app
USER scraper

# Expose Streamlit port
EXPOSE 8501

# Run the streamlit app when container starts
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
