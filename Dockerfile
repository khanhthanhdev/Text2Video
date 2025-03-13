FROM python:3.12-slim

# Install all dependencies in one layer
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
    texlive-full \
    dvisvgm \
    fonts-dejavu \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && which dvisvgm

WORKDIR /app

# Install uv for faster pip operations
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin:${PATH}"

# Copy virtual environment and project files
COPY requirements.txt .


# Activate the existing venv and install any missing packages
RUN uv venv /app/manimations \
    && . /app/manimations/bin/activate \
    && uv pip install --no-cache -r requirements.txt \
    && uv pip install --no-cache pycairo pangocffi manim

ENV PATH="/app/manimations/bin:${PATH}"
COPY *.py /app/
# Set environment variables
ENV PYTHONPATH=/app
ENV MPLBACKEND=Agg
ENV GRADIO_SERVER_NAME=0.0.0.0
ENV GRADIO_SERVER_PORT=7860

# Create directory for generated videos
RUN mkdir -p /app/generated_videos

# Copy .env file
COPY .env /app/.env

# Expose the port for the Gradio interface
EXPOSE 7860

# Command to run the application with the virtual environment
CMD ["/app/manimations/bin/python", "ai_agent.py"]