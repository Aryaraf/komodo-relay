# Gunakan base image Python
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy file aplikasi
COPY komodo_relay.py .

# Install dependensi
RUN pip install --no-cache-dir flask requests

# Expose port default Flask
EXPOSE 5000

# Jalankan aplikasi Flask
# Bisa override port lewat environment variable FLASK_PORT
CMD ["python", "komodo_relay.py"]
