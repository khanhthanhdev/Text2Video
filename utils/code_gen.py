"""
Utilities for generating Manim code.
"""
import re
import os
from config import get_openai_client, get_llm_model
from models import AnimationScenario
from utils.log import logger

def generate_code_direct(scenario):
    """
    Generate Manim code directly from an animation scenario.
    
    Args:
        scenario (AnimationScenario): Scenario object with animation details
        
    Returns:
        str: Generated Manim code
    """
    try:
        client = get_openai_client()
        llm = get_llm_model()
        
        # Create a prompt for the LLM based on the scenario
        prompt = f"""
        Generate Manim code for the following animation scenario:
        
        Title: {scenario.title}
        Description: {scenario.description}
        Complexity: {scenario.complexity}
        
        Create a self-contained Python script using the Manim library that:
        1. Creates a scene class that inherits from Scene
        2. Implements the construct method
        3. Creates necessary mathematical objects
        4. Animates them according to the description
        5. Uses appropriate colors, positioning, and timing
        6. Is fully executable with no errors
        
        Return only the Python code without any explanations or markdown formatting.
        """
        
        # Get code from LLM
        response = client.chat.completions.create(
            model=llm,
            messages=[
                {"role": "system", "content": "You are an expert in generating Manim animations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500
        )
        
        manim_code = response.choices[0].message.content
        
        # Remove markdown code blocks if present
        if "```python" in manim_code:
            code_pattern = r"```python\n(.*?)```"
            match = re.search(code_pattern, manim_code, re.DOTALL)
            if match:
                manim_code = match.group(1)
        elif "```" in manim_code:
            code_pattern = r"```\n(.*?)```"
            match = re.search(code_pattern, manim_code, re.DOTALL)
            if match:
                manim_code = match.group(1)
        
        return manim_code
        
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        return f"# Error generating Manim code\n# {str(e)}"