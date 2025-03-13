# Build stage
FROM python:3.12-slim AS builder

# Install only essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    curl \
    ca-certificates \
    python3-dev \
    pkg-config \
    libcairo2-dev \
    libpango1.0-dev \
    ffmpeg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /build

# Copy only requirements file first to leverage caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN uv venv /build/.venv \
    && . /build/.venv/bin/activate \
    && uv pip install --no-cache -r requirements.txt \
    && uv pip install --no-cache pycairo pangocffi \
    && uv pip install --no-cache manim \
    && find /build/.venv -name __pycache__ -type d -exec rm -rf {} +

# Create a manim executable script
RUN echo '#!/bin/bash\n/build/.venv/bin/python -m manim "$@"' > /build/.venv/bin/manim \
    && chmod +x /build/.venv/bin/manim

# Runtime stage
FROM python:3.12-slim

# Install only runtime dependencies - all in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libcairo2 \
    libpango1.0-0 \
    texlive-full \
    fonts-dejavu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from builder
COPY --from=builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Verify manim installation and create wrapper if needed
RUN python -c "import manim; print(f'Manim version: {manim.__version__}')" && \
    echo '#!/bin/bash\n/app/.venv/bin/python -m manim "$@"' > /app/.venv/bin/manim && \
    chmod +x /app/.venv/bin/manim

# Set environment variables early since they rarely change
ENV PYTHONPATH=/app
ENV MPLBACKEND=Agg
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

# Create directory for generated videos
RUN mkdir -p /app/generated_videos

# Copy application files - put these last since they change most frequently
COPY manimations /app/manimations
COPY .env /app/.env

# Expose the port for the Gradio interface
EXPOSE 7860

# Command to run the application
CMD ["python", "manimations/ai_agent.py"]