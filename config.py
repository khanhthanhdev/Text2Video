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

# Configure OpenAI client to use Together API
def get_openai_client():
    """Get configured OpenAI client using Together API."""
    client = openai.OpenAI(
        api_key=os.environ.get("TOGETHER_API_KEY"),
        base_url="https://api.together.xyz/v1",
    )
    return client

# Define available models

# Quality settings
QUALITY_SETTINGS = {
    "low_quality": {"flag": "-ql", "dir": "480p15"},
    "medium_quality": {"flag": "-qm", "dir": "720p30"},
    "high_quality": {"flag": "-qh", "dir": "1080p60"}
}

# Video output directory settings
def get_output_directories():
    # Detect if we're running on Hugging Face
    is_huggingface = os.environ.get("SPACE_ID") is not None
    
    # Use appropriate temp and output directories based on the environment
    if is_huggingface:
        base_temp = "/tmp"
        output_dir = "/tmp/videos"  # Use /tmp for HF Spaces
    else:
        base_temp = os.path.join(os.getcwd(), "tmp")
        output_dir = os.path.join(os.getcwd(), "videos")
    
    # Ensure directories exist with proper permissions
    os.makedirs(base_temp, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    
    return base_temp, output_dir

# Shared utility for rendering manim videos
def render_manim_video(code, quality="medium_quality"):
    """
    Render Manim code into a video file.
    
    Args:
        code (str): Manim Python code to render
        quality (str): Quality level - "low_quality", "medium_quality", or "high_quality"
        
    Returns:
        str: Path to the rendered video file or error message
    """
    try:
        base_temp, output_dir = get_output_directories()
        temp_dir = tempfile.mkdtemp(dir=base_temp)
        script_path = os.path.join(temp_dir, "manim_script.py")
        
        with open(script_path, "w") as f:
            f.write(code)
        
        class_name = None
        for line in code.split("\n"):
            if line.startswith("class ") and "Scene" in line:
                class_name = line.split("class ")[1].split("(")[0].strip()
                break
        
        if not class_name:
            return "Error: Could not identify the Scene class in the generated code."
        
        quality_flag = QUALITY_SETTINGS[quality]["flag"]
        quality_dir = QUALITY_SETTINGS[quality]["dir"]
        command = ["manim", quality_flag, script_path, class_name]
        
        logger.info(f"Executing command: {' '.join(command)}")
        
        result = subprocess.run(command, cwd=temp_dir, capture_output=True, text=True)
        
        logger.info(f"Manim stdout: {result.stdout}")
        logger.error(f"Manim stderr: {result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"Manim execution failed: {result.stderr}")
            return f"Error rendering video: {result.stderr}"
        
        media_dir = os.path.join(temp_dir, "media")
        videos_dir = os.path.join(media_dir, "videos")
        
        if not os.path.exists(videos_dir):
            return "Error: No video was generated. Check if Manim is installed correctly."
        
        scene_dirs = [d for d in os.listdir(videos_dir) if os.path.isdir(os.path.join(videos_dir, d))]
        
        if not scene_dirs:
            return "Error: No scene directory found in the output."
        
        scene_dir = max([os.path.join(videos_dir, d) for d in scene_dirs], key=os.path.getctime)
        
        mp4_files = [f for f in os.listdir(os.path.join(scene_dir, quality_dir)) if f.endswith(".mp4")]
        
        if not mp4_files:
            return "Error: No MP4 file was generated."
        
        video_file = max([os.path.join(scene_dir, quality_dir, f) for f in mp4_files], key=os.path.getctime)
        
        timestamp = int(time.time())
        output_file = os.path.join(output_dir, f"manim_video_{timestamp}.mp4")
        
        shutil.copy2(video_file, output_file)
        
        logger.info(f"Video generated: {output_file}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Error rendering video: {e}")
        return f"Error rendering video: {str(e)}"
    finally:
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.error(f"Error cleaning up temporary directory: {e}")
