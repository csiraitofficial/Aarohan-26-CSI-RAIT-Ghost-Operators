FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap-dev \
    tshark \
    && rm -rf /var/lib/apt/lists/*

# Security: Create non-root user
RUN groupadd -r nids && useradd -r -g nids nids

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set permissions
RUN mkdir -p logs data app/ml_models && \
    chown -R nids:nids /app

# Switch to non-root user 
# NOTE: Live packet capture may require 'cap_net_raw,cap_net_admin+eip' on the python binary
# which is handled at the OS/Kernel level or via Docker Capabilities
USER nids

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
