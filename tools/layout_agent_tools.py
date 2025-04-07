from agents import layout_agent
from models import AnimationPrompt, AnimationScenario
from config import DEFAULT_MODEL, logger, client, llm
import re
import json
from typing import Optional, Dict, Any
from pydantic_ai import RunContext
@layout_agent.tool
def analyze_element_layout(ctx: RunContext[AnimationPrompt], code: str) -> dict:
    """Analyze Manim code for potential layout issues and element positioning."""
    prompt = ctx.deps
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Analyze Manim code for layout issues and element positioning. Look for:
1. Overlapping elements or text
2. Elements positioned too close to each other
3. Elements positioned off-screen or at extreme edges
4. Poor use of screen space
5. Too many elements appearing simultaneously
6. Lack of clear positioning commands

Respond with a JSON object containing:
- issues: List of detected layout issues
- suggestions: List of positioning improvements
- animation_flow: List of animation sequence improvements
- spacing: Suggested minimum spacing between elements
- regions: Suggested screen regions to use for key elements
"""
            },
            {"role": "user", "content": f"Analyze this Manim code for layout issues:\n\n```python\n{code}\n```\n\nPrompt: {prompt.description}, Complexity: {prompt.complexity}"}
        ]
    )
    
    content = response.choices[0].message.content
    
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            analysis = json.loads(json_str)
            return analysis
    except Exception as e:
        logger.error(f"Error parsing layout analysis: {e}")
    
    # Fallback with default values
    return {
        "issues": ["Potential element overlap", "Undefined positioning"],
        "suggestions": ["Use explicit coordinates for all elements", "Add spacing between elements"],
        "animation_flow": ["Break complex animations into steps", "Add wait time between steps"],
        "spacing": 1.0,
        "regions": ["UP", "DOWN", "LEFT", "RIGHT", "CENTER"]
    }

@layout_agent.tool
def optimize_layout(ctx: RunContext[AnimationPrompt], code: str, analysis: dict) -> str:
    """Optimize the layout of elements in Manim code."""
    prompt = ctx.deps
    
    # Serialize the analysis for the prompt
    analysis_str = json.dumps(analysis, indent=2)
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Optimize the layout and animation flow in Manim code. Follow these rules:
1. Explicitly position ALL elements with coordinates (e.g., .move_to(), .shift(), .to_edge())
2. Ensure minimum spacing (1.0 units) between all elements
3. Use screen regions effectively (UP, DOWN, LEFT, RIGHT, UL, UR, DL, DR)
4. Group related elements using VGroup and arrange them logically
5. Break complex animations into steps with self.wait() between them
6. Use sequential animations for clarity (one concept at a time)
7. Use consistent positioning and transitions throughout the animation
8. Add comments explaining positioning choices

Preserve all mathematical content and educational purpose of the animation.
Only make changes to improve layout, positioning, and animation flow.
"""
            },
            {"role": "user", "content": f"Original code:\n\n```python\n{code}\n```\n\nOptimize the layout based on this analysis:\n{analysis_str}\n\nPrompt: {prompt.description}, Complexity: {prompt.complexity}\n\nReturn the optimized code that fixes all layout issues."}
        ]
    )
    
    optimized_code = response.choices[0].message.content
    
    # Clean up the response to extract just the code
    if "```python" in optimized_code:
        optimized_code = optimized_code.split("```python", 1)[1]
    if "```" in optimized_code:
        optimized_code = optimized_code.split("```", 1)[0]
    
    return optimized_code.strip()