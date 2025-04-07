"""
Rendering functionality for Manim animations.
"""

import os
import subprocess
import shutil
import uuid
import logging
from datetime import datetime

from config import get_output_directories, QUALITY_SETTINGS

logger = logging.getLogger(__name__)

def render_manim_video(code, quality="medium_quality"):
    """
    Render Manim code into a video.
    
    Args:
        code (str): The Manim code to render
        quality (str): The quality level (low_quality, medium_quality, high_quality)
        
    Returns:
        str: Path to the output video or error message
    """
    try:
        # Get appropriate directories
        base_temp, output_dir = get_output_directories()
        
        # Use a short random ID instead of the default long path from mkdtemp
        short_id = str(uuid.uuid4())[:8]  # Use only first 8 chars of UUID
        temp_dir = os.path.join(base_temp, short_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        script_path = os.path.join(temp_dir, "script.py")
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        # Extract class name from code
        class_name = None
        for line in code.split("\n"):
            if line.startswith("class ") and "Scene" in line:
                class_name = line.split("class ")[1].split("(")[0].strip()
                break
            
        if not class_name:
            return "Error: Could not identify the Scene class in the generated code."
        
        # Get quality settings
        quality_settings = QUALITY_SETTINGS.get(
            quality, 
            QUALITY_SETTINGS["medium_quality"]
        )
        
        # Build the manim command
        command = ["manim", quality_settings["flag"], script_path, class_name]
        quality_dir = quality_settings["dir"]
        
        logger.info(f"Executing command: {' '.join(command)}")
        
        # Run the command
        result = subprocess.run(command, cwd=temp_dir, capture_output=True, text=True)
        
        logger.info(f"Manim stdout: {result.stdout}")
        logger.error(f"Manim stderr: {result.stderr}")
        
        if result.returncode != 0:
            logger.error(f"Manim execution failed: {result.stderr}")
            return f"Error rendering video: {result.stderr}"
        
        # Find the output video
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
        
        # Use a shorter filename format with timestamp
        timestamp = datetime.now().strftime("%m%d%H%M")
        output_file = os.path.join(output_dir, f"vid_{timestamp}_{short_id}.mp4")
        
        shutil.copy2(video_file, output_file)
        
        logger.info(f"Video generated: {output_file}")
        
        return output_file
        
    except Exception as e:
        logger.error(f"Error rendering video: {e}")
        return f"Error: {str(e)}"
    finally:
        try:
            # Clean up temporary directory if it exists
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temporary directory: {e}")
