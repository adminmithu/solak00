FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Set working directory
WORKDIR /app

# Ensure unbuffered python output
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=10000 \
    HEADLESS=true

# Copy dependencies list
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Ensure Chromium browser is ready
RUN playwright install chromium

# Copy application source code
COPY . .

# Expose Render HTTP Port for health check & cron ping
EXPOSE 10000

# Start Telegram Bot application
CMD ["python", "main.py"]
