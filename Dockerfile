# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any are known - for now, none)
# RUN apt-get update && apt-get install -y --no-install-recommends some-package && rm -rf /var/lib/apt/lists/*

# Copy the requirements file first to leverage Docker cache
COPY src/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code into the container
COPY src/ /app/src/

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
# Using src.main:app assuming main.py is in src/ directory
# Added --workers 4 as a sensible default, can be configured.
CMD ["gunicorn", "src.main:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
