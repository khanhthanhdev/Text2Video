# Base image with Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for Manim
RUN apt-get update && apt-get install -y \
    ffmpeg \
    texlive-full \
    tipa \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libgif-dev \
    librsvg2-dev \
    pkg-config \
    gcc \
    libffi-dev \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Manim
RUN pip install --no-cache-dir manim

# Copy the application files
COPY manimations /app/manimations

# Create a sample .env file with placeholders for required environment variables
RUN echo "# Environment variables for Manimation Generator\nTOGETHER_API_KEY=your_api_key_here" > /app/.env

# Create directory for generated videos
RUN mkdir -p /app/generated_videos

# Set environment variables
ENV PYTHONPATH=/app
ENV MPLBACKEND=Agg

# Expose the port for the Gradio interface
EXPOSE 7860

# Command to run the application
CMD ["python", "manimations/ai_agent.py"]
