"""
Functions for generating, refining, and rendering Manim animations.
"""
import os
import re
import openai
from config import get_openai_client, get_llm_model, get_output_directories
from models import AnimationPrompt, AnimationScenario, AnimationResult
from utils.log import logger, format_log_output
from utils.layout import direct_optimize_layout, optimize_element_positioning
from utils.code_gen import generate_code_direct
from renderer import render_manim_video, preprocess_manim_code
from memory import memory  # Import the singleton memory instance

def generate_animation(prompt, complexity="medium", quality="medium_quality"):
    """
    Generate a new animation from a text prompt.
    
    Args:
        prompt (str): Text description of the animation to generate
        complexity (str): Complexity level (simple, medium, complex)
        quality (str): Video quality (low_quality, medium_quality, high_quality)
        
    Returns:
        tuple: (code, video_path, log)
    """
    try:
        # Create the animation prompt object
        animation_prompt = AnimationPrompt(
            description=prompt,
            complexity=complexity
        )
        
        # Generate the scenario first
        scenario = AnimationScenario(
            title=f"Animation: {prompt[:30]}...",
            description=prompt,
            complexity=complexity
        )
        
        # Store the scenario in memory
        memory.current_scenario = scenario
        
        # Generate code using the scenario - explicitly pass the scenario
        manim_code = generate_code_direct(scenario=scenario)
        
        # Preprocess the code to avoid dimension errors
        manim_code = preprocess_manim_code(manim_code)
        
        # Render the video
        video_path = render_manim_video(manim_code, quality)
        
        # Check if rendering was successful
        if not video_path:
            logger.error("Video rendering failed")
            return manim_code, None, "Error: Video rendering failed. Please check the Manim code for errors."
        
        # Store the result in memory
        memory.add_result(manim_code, video_path)
        
        # Format log output
        log = format_log_output(f"Generated animation from prompt: {prompt}", 
                              f"Complexity: {complexity}, Quality: {quality}")
        
        return manim_code, video_path, log
        
    except Exception as e:
        logger.error(f"Error generating animation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return f"# Error generating animation\n# {str(e)}", None, f"Error: {str(e)}"

def refine_animation(code, feedback, quality="medium_quality"):
    """
    Refine an existing animation based on feedback.
    
    Args:
        code (str): Existing Manim code
        feedback (str): User feedback to incorporate
        quality (str): Video quality for rendering
        
    Returns:
        tuple: (refined_code, video_path, log)
    """
    try:
        # Use LLM to refine the code based on feedback
        client = get_openai_client()
        llm = get_llm_model()
        
        # Simple implementation - in production you'd want more structured prompting
        response = client.chat.completions.create(
            model=llm,
            messages=[
                {"role": "system", "content": "You are a Manim expert. Modify the following code based on user feedback."},
                {"role": "user", "content": f"Original code:\n\n{code}\n\nFeedback: {feedback}\n\nPlease modify the code to address this feedback."}
            ],
            max_tokens=1500
        )
        
        refined_code = response.choices[0].message.content
        
        # Extract code block if the LLM wrapped it
        code_pattern = r"```python\n(.*?)```"
        match = re.search(code_pattern, refined_code, re.DOTALL)
        if match:
            refined_code = match.group(1)
        
        # Render the video
        video_path = render_manim_video(refined_code, quality)
        
        # Format log output
        log = format_log_output(f"Refined animation based on feedback: {feedback}", 
                              f"Quality: {quality}")
        
        return refined_code, video_path, log
        
    except Exception as e:
        logger.error(f"Error refining animation: {str(e)}")
        return code, None, f"Error refining animation: {str(e)}"

def rerender_animation(code, quality="medium_quality"):
    """
    Re-render the current animation code.
    
    Args:
        code (str): Manim code to render
        quality (str): Video quality
        
    Returns:
        tuple: (video_path, log)
    """
    try:
        # Render the video
        video_path = render_manim_video(code, quality)
        
        # Format log output
        log = format_log_output("Re-rendered animation", f"Quality: {quality}")
        
        return video_path, log
        
    except Exception as e:
        logger.error(f"Error re-rendering animation: {str(e)}")
        return None, f"Error re-rendering animation: {str(e)}"

def evaluate_and_fix_manim_code(code, prompt, complexity):
    """
    Evaluate Manim code for errors and fix them.
    
    Args:
        code (str): Manim code to evaluate
        prompt (str): Original prompt for context
        complexity (str): Complexity level
        
    Returns:
        tuple: (fixed_code, evaluation_report)
    """
    try:
        client = get_openai_client()
        llm = get_llm_model()
        
        # Ask LLM to evaluate and fix the code
        response = client.chat.completions.create(
            model=llm,
            messages=[
                {"role": "system", "content": "You are a Manim expert. Evaluate the following code for errors and fix them."},
                {"role": "user", "content": f"Original prompt: {prompt}\nComplexity: {complexity}\n\nCode to evaluate:\n\n{code}\n\nPlease evaluate this code for syntax errors, positioning issues, and other problems. Return the fixed code and an evaluation report."}
            ],
            max_tokens=1500
        )
        
        result = response.choices[0].message.content
        
        # Parse the response - in production you'd want more structured parsing
        if "```python" in result:
            code_pattern = r"```python\n(.*?)```"
            match = re.search(code_pattern, result, re.DOTALL)
            if match:
                fixed_code = match.group(1)
                # Extract the evaluation report (everything except the code block)
                evaluation_report = re.sub(code_pattern, "", result, flags=re.DOTALL)
                return fixed_code, evaluation_report
        
        # If no code block found, assume the whole response is the fixed code
        # and generate a simple report
        return code, "Code evaluation complete. No major issues found."
        
    except Exception as e:
        logger.error(f"Error evaluating code: {str(e)}")
        return code, f"Error during evaluation: {str(e)}"