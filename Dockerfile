FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first (for Docker caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy only the app folder (your FastAPI application)
COPY app /app/app

# Command to start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "900", "--timeout-graceful-shutdown", "900"]