FROM python:3.14-slim@sha256:63a4c7f612a00f92042cbdcc7cdc6a306f38485af0a200b9c89de7d9b1607d15
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
