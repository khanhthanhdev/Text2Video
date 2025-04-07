"""
Configuration settings and shared utilities for the Manimation project.
"""
import os
import openai
import tempfile
import subprocess
import shutil
import time
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Default model to use
DEFAULT_MODEL = "deepseek-ai/DeepSeek-V3"

AVAILABLE_MODELS = {
    "llama3": "meta-llama/Llama-3.1-8B-Instruct-Turbo",
    "deepseek": "deepseek-ai/DeepSeek-V3",
    "mixtral": "mistralai/Mixtral-8x7B-Instruct-v0.1",
}

AVAILABLE_PROVIDER = {
    "TogetherAI": "https://api.together.xyz/v1",
    "HuggingFace": "https://api-inference.huggingface.co/models",
    "Groq": "https://api.groq.com/v1",
    "Replicate": "https://api.replicate.com/v1",
    "OpenAI": "https://api.openai.com/v1",
}

def get_openai_client():
    """Get configured OpenAI client using Together API"""
    return openai.OpenAI(
        api_key=os.environ.get("TOGETHER_API_KEY"),
        base_url="https://api.together.xyz/v1",
    )

def get_llm_model():
    """Get the LLM model identifier"""
    return "deepseek-ai/DeepSeek-V3"

# Quality settings
QUALITY_SETTINGS = {
    "low_quality": {"flag": "-ql", "dir": "480p15"},
    "medium_quality": {"flag": "-qm", "dir": "720p30"},
    "high_quality": {"flag": "-qh", "dir": "1080p60"}
}

def get_output_directories():
    """Get output directories for videos and temp files"""
    # Check if we're running on Hugging Face
    is_huggingface = os.environ.get("SPACE_ID") is not None
    
    # Use appropriate directories based on environment
    if is_huggingface:
        # Use /tmp directory for HF Spaces which has write permissions
        video_dir = os.path.join("/tmp", "videos")
        temp_dir = os.path.join("/tmp", "manim_temp")
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
    else:
        video_dir = os.path.join(os.getcwd(), "videos")
        temp_dir = os.path.join(os.getcwd(), "tmp")
        os.makedirs(video_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
    
    return {
        "video_dir": video_dir,
        "temp_dir": temp_dir
    }

# Shared utility for rendering manim videos
def render_manim_video(code, quality="medium_quality"):
    """Render Manim video - placeholder for actual implementation"""
    # This is a stub that should be implemented or imported elsewhere
    pass
