"""
Animation generation functionality for the Manimation system.
"""

import logging
from pydantic_ai import RunContext

from models import AnimationPrompt, AnimationScenario
from tools import extract_scenario_direct, generate_code_direct, direct_optimize_layout
from renderer import render_manim_video
from formatting import format_log_output
from memory import ConversationMemory

# Configure logging
logger = logging.getLogger(__name__)

def generate_animation(prompt: str, complexity: str = "medium", quality: str = "medium_quality", 
                      memory: ConversationMemory = None) -> tuple:
    """
    Generate an animation from a text prompt.
    
    Args:
        prompt: The text description of what to animate
        complexity: Complexity level (simple, medium, complex)
        quality: Video quality level
        memory: Optional conversation memory instance
        
    Returns:
        tuple: (code, video_path, log_output)
    """
    try:
        # Create prompt object with complexity
        prompt_obj = AnimationPrompt(description=prompt, complexity=complexity)
        
        # Extract scenario (use direct method)
        scenario = extract_scenario_direct(prompt, complexity)
        
        # Generate Manim code
        code = generate_code_direct(prompt, scenario, complexity)
        
        # Try to optimize layout (might fail silently and return original code)
        try:
            optimized_code = direct_optimize_layout(code, prompt, complexity)
            if optimized_code and "from manim import" in optimized_code:
                code = optimized_code
        except Exception as e:
            logger.error(f"Error during layout optimization: {e}")
            # Continue with original code if optimization fails
        
        # Render the video
        video_path = render_manim_video(code, quality)
        
        # Format the log output
        log_output = format_log_output(scenario, code)
        
        # Store in memory if provided
        if memory:
            memory.add_interaction(prompt, scenario, code, video_path)
        
        return code, video_path, log_output
        
    except Exception as e:
        logger.error(f"Error generating animation: {e}")
        return f"Error: {str(e)}", None, f"Error occurred: {str(e)}"

def refine_animation(code: str, feedback: str, quality: str = "medium_quality", 
                    memory: ConversationMemory = None) -> tuple:
    """
    Refine an existing animation based on feedback.
    
    Args:
        code: The existing Manim code
        feedback: User feedback for refinement
        quality: Video quality level
        memory: Optional conversation memory instance
        
    Returns:
        tuple: (refined_code, video_path, log_output)
    """
    try:
        # Get prompt and context information from memory if available
        prompt = "Mathematical animation"
        context = ""
        if memory:
            prompt = memory.get_last_prompt()
            context = memory.get_context_for_refinement()
        
        # Special case for layout/positioning feedback
        if any(keyword in feedback.lower() for keyword in ["position", "layout", "overlap", "spacing", "step by step", "clear"]):
            from tools import optimize_element_positioning
            refined_code = optimize_element_positioning(code, prompt, "medium")
        else:
            # Use OpenAI to refine the code based on feedback
            from config import get_openai_client
            client = get_openai_client()
            
            response = client.chat.completions.create(
                model="deepseek-ai/DeepSeek-V3",
                messages=[
                    {"role": "system", "content": """
You are a Manim code expert. Your task is to refine animation code based on user feedback.
Keep the overall structure and purpose of the animation, but implement the changes requested.
Make sure the code remains valid and follows Manim best practices.

IMPORTANT REQUIREMENTS:
1. Only return the complete, corrected Manim code
2. Ensure class name and structure remains consistent
3. All changes must be compatible with Manim Community edition
4. Do not explain your changes in comments outside of helpful inline comments
"""
                    },
                    {"role": "user", "content": f"Here is the current Manim animation code:\n\n```python\n{code}\n```\n\n{context}\nPlease refine this code based on this feedback: \"{feedback}\"\n\nReturn only the improved code."}
                ]
            )
            
            refined_code = response.choices[0].message.content.strip()
            
            # Remove any markdown code formatting if present
            if refined_code.startswith("```python"):
                refined_code = refined_code.split("```python", 1)[1]
            if refined_code.endswith("```"):
                refined_code = refined_code.rsplit("```", 1)[0]
            
            refined_code = refined_code.strip()
        
        # Render the refined code
        video_path = render_manim_video(refined_code, quality)
        
        if video_path and not video_path.startswith("Error"):
            # Update memory with refined code if provided
            if memory and memory.current_scenario:
                memory.current_code = refined_code
            
            return refined_code, video_path, f"## Refined Animation\n\nFeedback incorporated: \"{feedback}\"\n\nAnimation successfully rendered."
        else:
            return refined_code, None, f"## Error in Rendering\n\n```\n{video_path}\n```\n\nPlease check your code for errors."
    
    except Exception as e:
        logger.error(f"Error refining animation: {e}")
        return code, None, f"## Error in Refinement\n\n```\n{str(e)}\n```\n\nPlease try again with different feedback."

def evaluate_and_fix_manim_code(code: str, prompt: str, complexity: str = "medium") -> tuple:
    """
    Evaluate Manim code for errors and fix if needed.
    
    Args:
        code: Manim code to evaluate
        prompt: The original prompt
        complexity: Complexity level
        
    Returns:
        tuple: (fixed_code, evaluation_report)
    """
    from tools import direct_evaluate_and_fix
    return direct_evaluate_and_fix(code, prompt, complexity)

def rerender_animation(code: str, quality: str = "medium_quality") -> tuple:
    """
    Re-render animation with user-edited code.
    
    Args:
        code: Manim code to render
        quality: Video quality
        
    Returns:
        tuple: (video_path, status_message)
    """
    try:
        video_path = render_manim_video(code, quality)
        if video_path and not video_path.startswith("Error"):
            return video_path, f"## Re-rendered Animation\n\nCode successfully rendered to video.\n\nCheck the video player for results."
        else:
            return None, f"## Error in Rendering\n\n```\n{video_path}\n```\n\nPlease check your code for errors."
    except Exception as e:
        logger.error(f"Error re-rendering animation: {e}")
        return None, f"## Error in Rendering\n\n```\n{str(e)}\n```\n\nPlease try again with different code."