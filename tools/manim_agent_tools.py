from agents import manim_agent
from models import AnimationPrompt, AnimationScenario
from config import DEFAULT_MODEL, logger, client, llm, render_manim_video
import re
import json
from typing import Optional, Dict, Any
from pydantic_ai import RunContext

@manim_agent.tool
def extract_scenario(ctx: RunContext[AnimationPrompt]) -> AnimationScenario:
    """Extract a structured animation scenario from a text prompt."""
    prompt = ctx.deps  # Get the AnimationPrompt from context
    
    # Use Together API with OpenAI client
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Create a storyboard for a math/physics educational animation. Focus on making concepts clear for beginners.

Respond with a JSON object containing:
- title: A clear, engaging title
- objects: Mathematical objects to include (e.g., "coordinate_plane", "function_graph")
- transformations: Animation types to use (e.g., "fade_in", "transform")
- equations: Mathematical equations to feature (can be null)
- storyboard: 5-7 sections, each with:
  * section_name: Section name (e.g., "Introduction")
  * time_range: Timestamp range (e.g., "0:00-2:00")
  * narration: What the narrator says
  * visuals: What appears on screen
  * animations: Specific animations
  * key_points: 1-2 main takeaways

Include: introduction, simple explanation, detailed walkthrough, examples, and conclusion.

Use everyday analogies, define technical terms, and focus on visualization.

Only respond with the JSON object, nothing else.
"""},
            {"role": "user", "content": f"Create an animation storyboard for: '{prompt.description}'. "
                                        f"Complexity level: {prompt.complexity}. Make it beginner-friendly "
                                        f"with clear explanations and visual examples."}
        ]
    )
    content = response.choices[0].message.content
    
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            scenario_dict = json.loads(json_str)
            
            # Get basic scenario info
            title = scenario_dict.get('title', f"{prompt.description.capitalize()} Visualization")
            objects = scenario_dict.get('objects', [])
            transformations = scenario_dict.get('transformations', [])
            equations = scenario_dict.get('equations', None)
            
            # Store the storyboard in logger
            if 'storyboard' in scenario_dict:
                logger.info(f"Generated storyboard: {json.dumps(scenario_dict['storyboard'], indent=2)}")
            
            return AnimationScenario(
                title=title,
                objects=objects,
                transformations=transformations,
                equations=equations
            )
    except Exception as e:
        logger.error(f"Error parsing scenario JSON: {e}")
    
    # Fallback with default values
    return AnimationScenario(
        title=f"{prompt.description.capitalize()} Visualization",
        objects=["circle", "text", "coordinate_system"],
        transformations=["creation", "transformation", "highlight"],
        equations=None
    )

# Also simplify extract_scenario_direct with the same approach
def extract_scenario_direct(prompt: str, complexity: str = "medium") -> AnimationScenario:
    """Direct implementation of scenario extraction without using RunContext."""
    # Use Together API with OpenAI client
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Create a storyboard for a math/physics educational animation. Focus on making concepts clear for beginners.

Respond with a JSON object containing:
- title: A clear, engaging title
- objects: Mathematical objects to include (e.g., "coordinate_plane", "function_graph")
- transformations: Animation types to use (e.g., "fade_in", "transform")
- equations: Mathematical equations to feature (can be null)
- storyboard: 5-7 sections, each with:
  * section_name: Section name (e.g., "Introduction")
  * time_range: Timestamp range (e.g., "0:00-2:00")
  * narration: What the narrator says
  * visuals: What appears on screen
  * animations: Specific animations
  * key_points: 1-2 main takeaways

Include: introduction, simple explanation, detailed walkthrough, examples, and conclusion.

Use everyday analogies, define technical terms, and focus on visualization.

Only respond with the JSON object, nothing else.
"""},
            {"role": "user", "content": f"Create an animation storyboard for: '{prompt}'. "
                                        f"Complexity level: {complexity}. Make it beginner-friendly "
                                        f"with clear explanations and visual examples."}
        ]
    )
    content = response.choices[0].message.content
    
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            scenario_dict = json.loads(json_str)
            
            # Get basic scenario info
            title = scenario_dict.get('title', f"{prompt.capitalize()} Visualization")
            objects = scenario_dict.get('objects', [])
            transformations = scenario_dict.get('transformations', [])
            equations = scenario_dict.get('equations', None)
            
            # Store the storyboard in logger
            if 'storyboard' in scenario_dict:
                logger.info(f"Generated storyboard: {json.dumps(scenario_dict['storyboard'], indent=2)}")
            
            return AnimationScenario(
                title=title,
                objects=objects,
                transformations=transformations,
                equations=equations
            )
    except Exception as e:
        logger.error(f"Error parsing scenario JSON: {e}")
    
    # Fallback based on keywords in prompt
    objects = ["circle", "text", "coordinate_system"]
    transformations = ["creation", "transformation", "highlight"]
    equations = None
    
    if any(kw in prompt.lower() for kw in ["triangle", "pythagorean"]):
        objects = ["triangle", "square", "text"]
        transformations = ["creation", "area_calculation"]
        equations = ["a^2 + b^2 = c^2"]
    elif any(kw in prompt.lower() for kw in ["calculus", "derivative", "integral"]):
        objects = ["function_graph", "tangent_line", "area"]
        transformations = ["drawing", "zoom", "fill"]
        equations = ["f'(x) = \\lim_{h \\to 0}\\frac{f(x+h) - f(x)}{h}"]
    
    return AnimationScenario(
        title=f"{prompt.capitalize()} Visualization",
        objects=objects,
        transformations=transformations,
        equations=equations
    )

@manim_agent.tool
def generate_code(ctx: RunContext[AnimationPrompt], scenario: AnimationScenario) -> str:

    """Generate Manim code from a structured scenario."""
    # Use OpenAI to generate Manim code
    objects_str = ", ".join(scenario.objects)
    transformations_str = ", ".join(scenario.transformations)
    equations_str = ", ".join(scenario.equations) if scenario.equations else "No equations"
    
    prompt_description = ctx.deps.description  # Access the original prompt
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": "Generate Manim code for mathematical animations."},
            {"role": "user", "content": f"Create Manim code for an animation titled '{scenario.title}' "
                                       f"with objects: {objects_str}, transformations: {transformations_str}, "
                                       f"and equations: {equations_str}. Original request: '{prompt_description}'"}
        ]
    )
    return response.choices[0].message.content


@manim_agent.tool_plain
def render_animation(code: str, quality="medium_quality") -> str:
    """Render Manim code into a video. This doesn't need the context."""
    return render_manim_video(code, quality)


