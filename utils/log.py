"""
Logging utilities for the Manimation application.
"""
import logging
import sys
from typing import Optional, Any, Dict, List
from models import AnimationScenario  # Import from local models instead

# Configure the logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create a logger instance
logger = logging.getLogger(__name__)

def format_log_output(title: str, details: str = "", scenario = None):
    """
    Format log output for display in the UI.
    
    Args:
        title (str): Main title or summary
        details (str): Additional details
        scenario (AnimationScenario, optional): Animation scenario object
        
    Returns:
        str: Formatted log output as markdown
    """
    # Start with the title and details
    formatted_output = f"## {title}\n\n"
    
    if details:
        formatted_output += f"{details}\n\n"
    
    # Add scenario information if provided
    if scenario:
        # Only try to process scenario.objects if scenario is not a string
        # and has an objects attribute
        formatted_output += f"### Scenario: {getattr(scenario, 'title', 'No title')}\n\n"
        
        # Check if scenario has a description
        if hasattr(scenario, 'description'):
            formatted_output += f"{scenario.description}\n\n"
        
        # Check if scenario has objects
        if hasattr(scenario, 'objects') and scenario.objects:
            formatted_output += "### Elements:\n\n"
            try:
                for obj in scenario.objects:
                    if isinstance(obj, dict):
                        # Handle dictionary objects
                        obj_name = obj.get('name', 'Unknown')
                        obj_type = obj.get('type', 'Unknown')
                        formatted_output += f"- **{obj_name}** ({obj_type})\n"
                    else:
                        # Handle other object types
                        formatted_output += f"- {str(obj)}\n"
            except (AttributeError, TypeError) as e:
                # If there's an error processing objects, log it but continue
                logger.warning(f"Error processing scenario objects: {str(e)}")
    
    return formatted_output

def log_animation_details(animation_result, prompt=None):
    """
    Log details about an animation result.
    
    Args:
        animation_result (AnimationResult): Result object
        prompt (str, optional): Original prompt
    """
    logger.info(f"Animation generated from prompt: {prompt or 'Unknown'}")
    
    if animation_result:
        if hasattr(animation_result, 'video_path') and animation_result.video_path:
            logger.info(f"Video saved to: {animation_result.video_path}")
        
        if hasattr(animation_result, 'error') and animation_result.error:
            logger.error(f"Animation error: {animation_result.error}")