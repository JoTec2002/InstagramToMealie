FROM python:3.14-slim@sha256:cea0e6040540fb2b965b6e7fb5ffa00871e632eef63719f0ea54bca189ce14a6
LABEL authors="JoTec2002"

WORKDIR /app

# Install system packages needed for Playwright and Chromium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates \
    fonts-liberation \
    fonts-unifont \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1

COPY requirements.txt /app/

# Install required packages
RUN pip install -r requirements.txt

# Install Playwright and browser binaries
RUN python -m playwright install chromium

# Copy application code
COPY main.py /app/
COPY templates /app/templates
COPY helpers /app/helpers
COPY static /app/static

# Expose the Flask port
EXPOSE 9001

# Run the application
CMD ["python", "-u", "main.py"]
