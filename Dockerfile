# Dockerfile for peripheral-mcp FastAPI server
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml ./
COPY requirements.txt ./
COPY src/ ./src/

# Install dependencies
RUN uv pip install --system -r requirements.txt

# Expose port
EXPOSE 8080

# Run cloud MCP server
CMD ["uvicorn", "src.mcp.cloud_server:app", "--host", "0.0.0.0", "--port", "8080"]
