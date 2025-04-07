"""
Manim rendering utilities for the Manimation application.
"""
import os
import subprocess
import tempfile
import uuid
import shutil
import logging
import re
import inspect
from config import get_output_directories, QUALITY_SETTINGS

# Set up logging
logger = logging.getLogger(__name__)

def check_latex_installation():
    """Check if LaTeX is properly installed and configured"""
    try:
        result = subprocess.run(
            ["latex", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        # If there's an error, assume LaTeX is not properly installed
        return False

def preprocess_manim_code(code):
    """
    Preprocess Manim code to avoid common errors.
    
    Args:
        code (str): Original Manim code
        
    Returns:
        str: Preprocessed code
    """
    # Fix dimension mismatches in array operations
    # Look for common patterns like color arrays or positioning
    
    # 1. Fix RGB color definitions that might cause broadcast errors
    # Replace RGB(a, b) with RGB(a, b, 0) to ensure 3D vectors
    code = re.sub(r'RGB\s*\(\s*([^,]+)\s*,\s*([^)]+)\s*\)', r'RGB(\1, \2, 0)', code)
    
    # 2. Fix array operations with dimension mismatches
    # This is a simplified fix - in practice you would need more sophisticated analysis
    # Look for np.array operations with 2D arrays that might be combined with 3D arrays
    code = re.sub(r'np\.array\(\[([^]]+),\s*([^]]+)\]\)', r'np.array([\1, \2, 0])', code)
    
    # 3. Handle LaTeX-related issues by providing fallbacks for text
    # If we detect LaTeX issues in the environment, replace LaTeX with Text
    if not check_latex_installation():
        # Replace Tex and MathTex with Text when possible
        code = re.sub(r'Tex\(r"([^"]+)"\)', r'Text("\1")', code)
        code = re.sub(r'MathTex\(r"([^"]+)"\)', r'Text("\1")', code)
    
    return code

def extract_scene_name(code):
    """
    Extract the name of the Scene class from the code.
    
    Args:
        code (str): Manim Python code
        
    Returns:
        str: Name of the Scene class or None if not found
    """
    # Use regex to find class definitions that inherit from Scene
    scene_pattern = r'class\s+(\w+)\s*\(\s*Scene\s*\)'
    match = re.search(scene_pattern, code)
    
    if match:
        return match.group(1)
    return None

def render_manim_video(code, quality="medium_quality"):
    """
    Render Manim code to a video file.
    
    Args:
        code (str): Manim Python code to render
        quality (str): Video quality (low_quality, medium_quality, high_quality)
        
    Returns:
        str: Path to the rendered video file or None if rendering failed
    """
    if not code or not isinstance(code, str):
        logger.error(f"Invalid code provided: {type(code)}")
        return None
    
    # Preprocess the code to avoid common errors
    processed_code = preprocess_manim_code(code)
    
    # Get output directories from config
    dirs = get_output_directories()
    video_dir = dirs["video_dir"]
    temp_dir = dirs["temp_dir"]
    
    # Create a unique ID for this rendering
    render_id = str(uuid.uuid4().hex)[:8]
    
    # Create a dedicated directory for this render
    render_dir = os.path.join(temp_dir, render_id)
    os.makedirs(render_dir, exist_ok=True)
    
    # Define the script filename - Manim uses this name for output directories
    script_filename = "scene.py"
    script_path = os.path.join(render_dir, script_filename)
    
    # Write the code to the script file
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(processed_code)
    
    # Extract the scene name from the code
    scene_name = extract_scene_name(processed_code)
    if not scene_name:
        logger.error("Could not find a Scene class in the provided code")
        return None
    
    # Get quality settings
    quality_settings = QUALITY_SETTINGS.get(quality, QUALITY_SETTINGS["medium_quality"])
    quality_flag = quality_settings["flag"]
    quality_dir = quality_settings["dir"]
    
    # Add environment variable to skip MiKTeX update check
    env = os.environ.copy()
    env["MIKTEX_ADMIN_NO_UPDATE_CHECK"] = "1"
    
    # Ensure the output video directory exists
    os.makedirs(video_dir, exist_ok=True)
    
    # Create the output video filename
    output_video = os.path.join(video_dir, f"{render_id}.mp4")
    
    # Manim command with explicit output file
    cmd = [
        "manim",
        script_path,
        scene_name,
        quality_flag,
        "-o", output_video,  # Specify output file directly when possible
        "-v", "DEBUG"        # Use DEBUG level to see more output for troubleshooting
    ]
    
    logger.info(f"Rendering with command: {' '.join(cmd)}")
    logger.info(f"Working directory: {render_dir}")
    logger.info(f"Expected output: {output_video}")
    
    try:
        # Run the command in the render directory
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=render_dir
        )
        stdout, stderr = process.communicate()
        
        # Log the full output for debugging
        if stdout:
            logger.info(f"Manim stdout: {stdout}")
        if stderr:
            logger.error(f"Manim stderr: {stderr}")
        
        # Check if the process was successful
        if process.returncode != 0:
            logger.error(f"Manim execution failed with return code: {process.returncode}")
            
            # Create a simple error video if rendering fails
            return None
        
        # Check for direct output file first
        if os.path.exists(output_video):
            logger.info(f"Found output video at specified path: {output_video}")
            return output_video
        
        # Look for the video in Manim's standard output structure
        # Manim typically creates files in: media/videos/[script_name_without_extension]/[quality]/[scene_name].mp4
        script_name_without_ext = os.path.splitext(script_filename)[0]
        
        # List of possible paths where Manim might have created the video
        possible_paths = [
            # Standard Manim path (filename based)
            os.path.join(render_dir, "media", "videos", script_name_without_ext, quality_dir),
            # Alternative path with scene name
            os.path.join(render_dir, "media", "videos", scene_name, quality_dir),
            # Some versions might put it directly in media/videos
            os.path.join(render_dir, "media", "videos", quality_dir),
            # Or in videos/
            os.path.join(render_dir, "videos", quality_dir),
            # Last resort - any media directory
            os.path.join(render_dir, "media")
        ]
        
        # Search for any MP4 files in possible locations
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"Checking directory: {path}")
                
                # Look for .mp4 files
                if os.path.isdir(path):
                    video_files = [f for f in os.listdir(path) if f.endswith(".mp4")]
                    if video_files:
                        source_video = os.path.join(path, video_files[0])
                        logger.info(f"Found video file: {source_video}")
                        
                        # Copy to output location
                        shutil.copy2(source_video, output_video)
                        logger.info(f"Successfully copied video to: {output_video}")
                        return output_video
        
        # If we get here, do a full recursive search for any MP4 files
        logger.info("Performing full recursive search for MP4 files")
        for root, _, files in os.walk(render_dir):
            for file in files:
                if file.endswith(".mp4"):
                    source_video = os.path.join(root, file)
                    logger.info(f"Found video in recursive search: {source_video}")
                    
                    # Copy to output location
                    shutil.copy2(source_video, output_video)
                    logger.info(f"Successfully copied video to: {output_video}")
                    return output_video
        
        logger.error("No video files found after rendering")
        return None
        
    except Exception as e:
        logger.error(f"Error during rendering: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None
