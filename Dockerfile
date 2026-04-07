# Use bookworm for better registry stability during hackathons
FROM python:3.10-bookworm

WORKDIR /app

# Step 1: Copy the requirements from the ROOT, not server/
COPY requirements.txt .

# Step 2: Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Step 3: Copy everything else
COPY . .

# Step 4: Set paths correctly
ENV PYTHONPATH="/app"

# Standard HF Port
EXPOSE 7860

# Keep your healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health')"

# Start the environment server
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]