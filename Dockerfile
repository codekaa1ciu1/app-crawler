# Dockerfile for App Crawler Web Portal
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app_crawler/ ./app_crawler/
COPY web_portal/ ./web_portal/
COPY example_crawl.py .
COPY setup.py .
COPY README.md .

# Install the package
RUN pip install -e .

# Expose web portal port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=web_portal/app.py
ENV FLASK_ENV=production

# Create directories for data
RUN mkdir -p /app/screenshots /app/data

# Default command runs the web portal
CMD ["python", "web_portal/app.py"]
