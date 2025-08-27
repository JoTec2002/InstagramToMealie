FROM python:3.12-slim
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

# Expose the Flask port
EXPOSE 9001

# Run the application
CMD ["python", "-u", "main.py"]
