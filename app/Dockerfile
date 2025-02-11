FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the requirements file first (for Docker caching)
COPY requirements.txt /app/requirements.txt 

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# Copy the entire fastapp directory into /app/fastapp
COPY . /app/app

# Command to start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "900", "--timeout-graceful-shutdown", "900"]