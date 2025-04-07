"""
AI Agent for generating Manim animations from text prompts using pydantic-ai.
"""
import os
from typing import List, Optional
from dotenv import load_dotenv
import gradio as gr
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
import openai
import tempfile
import subprocess
import logging
from datetime import datetime
import shutil
import time
from io import StringIO
import re
import json
import logging
from models import AnimationPrompt, AnimationScenario, AnimationResult, LayoutConfiguration, EvaluationResult
from config import get_openai_client, get_output_directories, render_manim_video

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
llm = "deepseek-ai/DeepSeek-V3"

# Define Pydantic models for structured data
class AnimationPrompt(BaseModel):
    """User input for animation generation."""
    description: str = Field(..., description="Text description of the mathematical or physics concept to animate")
    complexity: str = Field("medium", description="Desired complexity of the animation")
    
class AnimationScenario(BaseModel):
    """Structured scenario for animation generation."""
    title: str = Field(..., description="Title of the animation")
    objects: List[str] = Field(..., description="Mathematical objects to include in the animation")
    transformations: List[str] = Field(..., description="Transformations to apply to the objects")
    equations: Optional[List[str]] = Field(None, description="Mathematical equations to visualize")
    
class AnimationResult(BaseModel):
    """Result of animation generation."""
    code: str = Field(..., description="Generated Manim code")
    video_path: str = Field(..., description="Path to the generated video file")

# New layout configuration model
class LayoutConfiguration(BaseModel):
    """Configuration for layout optimization of animation elements."""
    min_spacing: float = Field(0.5, description="Minimum spacing between elements in Manim units")
    vertical_alignment: List[str] = Field(["TOP", "CENTER", "BOTTOM"], description="Vertical alignment options")
    horizontal_alignment: List[str] = Field(["LEFT", "CENTER", "RIGHT"], description="Horizontal alignment options")
    staggered_animations: bool = Field(True, description="Whether to stagger animations for better clarity")
    screen_regions: List[str] = Field(["UL", "UP", "UR", "LEFT", "CENTER", "RIGHT", "DL", "DOWN", "DR"], 
                                     description="Screen regions for element positioning")
    canvas_size: tuple = Field((14, 8), description="Canvas size in Manim units (width, height)")

# New evaluation result model
class EvaluationResult(BaseModel):
    """Results of code evaluation."""
    has_errors: bool = Field(False, description="Whether the code has any errors")
    syntax_errors: List[str] = Field([], description="Syntax errors found in the code")
    positioning_issues: List[str] = Field([], description="Issues with element positioning")
    overlap_issues: List[str] = Field([], description="Potential element overlaps")
    suggestions: List[str] = Field([], description="Suggestions for improvement")
    fixed_code: Optional[str] = Field(None, description="Fixed code if available")

model = OpenAIModel(
    'deepseek-ai/DeepSeek-V3',
    provider=OpenAIProvider(
        base_url='https://api.together.xyz/v1', api_key=os.environ.get('TOGETHER_API_KEY')
    ),
)
# Create the agent with a static system prompt
manim_agent = Agent(
    model,  # or use Together API as needed
    deps_type=AnimationPrompt,  # Use AnimationPrompt as dependency type
    system_prompt=(
        "You are a specialized AI agent for creating mathematical animations. "
        "Your goal is to convert user descriptions into precise Manim code "
        "that visualizes mathematical and physics concepts clearly and elegantly."
    ),
)

# Create a layout optimization agent
layout_agent = Agent(
    model,
    deps_type=AnimationPrompt,
    system_prompt=(
        "You are a specialized AI agent for optimizing layout and animations in Manim code. "
        "Your goal is to analyze and improve element positioning, prevent overlaps, "
        "and create step-by-step animations that are clear and educational. "
        "You understand how to use Manim's coordinate system and positioning methods effectively."
    ),
)

# Create an evaluation agent
evaluation_agent = Agent(
    model,
    deps_type=AnimationPrompt,
    system_prompt=(
        "You are a specialized AI agent for evaluating Manim animation code. "
        "Your goal is to detect errors, check for proper element positioning, "
        "and ensure the code follows best practices for clear mathematical animations. "
        "You understand Manim's syntax and common pitfalls in animation creation."
    ),
)

# Configure OpenAI client to use Together API
client = openai.OpenAI(
    api_key=os.environ.get("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1",
)

# Add dynamic system prompts
@manim_agent.system_prompt
def add_complexity_guidance(ctx: RunContext[AnimationPrompt]) -> str:
    """Add guidance based on requested complexity."""
    complexity = ctx.deps.complexity
    if complexity == "simple":
        return (
            "Create simple, easy-to-understand animations with minimal elements. "
            "Focus on clarity over sophistication."
        )
    elif complexity == "complex":
        return (
            "Create sophisticated animations with multiple mathematical elements and transformations. "
            "You can use advanced Manim features and complex mathematical concepts."
        )
    else:  # medium
        return (
            "Balance clarity and sophistication in your animations. "
            "Include enough detail to illustrate the concept clearly without overwhelming the viewer."
        )

@manim_agent.system_prompt
def add_timestamp() -> str:
    """Add a timestamp to the system prompt."""
    return f"Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@layout_agent.system_prompt
def add_layout_guidance(ctx: RunContext[AnimationPrompt]) -> str:
    """Add layout guidance based on complexity."""
    complexity = ctx.deps.complexity
    if complexity == "simple":
        return (
            "Optimize layout for simple animations with minimal elements. "
            "Use large spacing and clear positioning. "
            "Each step should be very distinct and have ample wait time between transitions."
        )
    elif complexity == "complex":
        return (
            "Optimize layout for complex animations with many elements. "
            "Use thoughtful positioning with elements grouped by relevance. "
            "Break animations into logical steps with clear transitions between concepts."
        )
    else:  # medium
        return (
            "Balance spacing and density in your layout. "
            "Position elements with sufficient spacing while utilizing screen space efficiently. "
            "Present animations in a step-by-step manner with appropriate timing."
        )

@evaluation_agent.system_prompt
def add_evaluation_guidance(ctx: RunContext[AnimationPrompt]) -> str:
    """Add evaluation guidance based on complexity."""
    complexity = ctx.deps.complexity
    if complexity == "simple":
        return (
            "Focus on finding basic errors and ensuring clear positioning of minimal elements. "
            "Simple animations should have ample spacing and no overlapping elements."
        )
    elif complexity == "complex":
        return (
            "Look for subtle issues in complex code, including potential element overlaps "
            "when multiple transformations occur. Check for proper timing between steps "
            "and verify that complex mathematical notations are correctly formatted."
        )
    else:  # medium
        return (
            "Balance between checking for technical errors and verifying good animation principles. "
            "Ensure elements are properly spaced and animations follow a logical step-by-step flow."
        )

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

@evaluation_agent.tool
def check_syntax_errors(ctx: RunContext[AnimationPrompt], code: str) -> List[str]:
    """Check for Python and Manim-specific syntax errors."""
    prompt = ctx.deps
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Analyze this Manim code for syntax errors and logical mistakes. Look for:

1. Python syntax errors (missing colons, parentheses, indentation problems)
2. Manim-specific errors (incorrect class usage, invalid animation methods)
3. Undefined variables or objects that are used before definition
4. Incorrect parameter types or values
5. Missing imports or misused Manim classes
6. LaTeX syntax errors in MathTex objects
7. Animation errors (using wrong objects in animations, incorrect method calls)

For each error found, provide:
1. The line number or code region with the error
2. A description of what's wrong
3. A suggested fix

Be thorough but only focus on actual errors, not style issues.
"""
            },
            {"role": "user", "content": f"Check this Manim code for syntax errors:\n\n```python\n{code}\n```\n\nPrompt: {prompt.description}, Complexity: {prompt.complexity}"}
        ]
    )
    
    # Extract errors from response
    error_content = response.choices[0].message.content
    error_lines = error_content.split('\n')
    
    # Filter for actual errors
    errors = []
    current_error = ""
    for line in error_lines:
        if line.strip().startswith(("Error", "Issue", "Problem", "Bug", "Line", "1.", "2.", "3.", "4.", "5.")):
            if current_error:
                errors.append(current_error.strip())
            current_error = line.strip()
        elif current_error and line.strip():
            current_error += " " + line.strip()
    
    # Add the last error if there is one
    if current_error:
        errors.append(current_error.strip())
    
    return errors

@evaluation_agent.tool
def check_positioning(ctx: RunContext[AnimationPrompt], code: str) -> dict:
    """Check for proper positioning and potential overlaps in the animation."""
    prompt = ctx.deps
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Analyze this Manim code specifically for positioning and spacing issues. Look for:

1. Objects without explicit position commands (move_to, shift, to_edge, etc.)
2. Elements that might overlap based on their coordinates
3. Text or equations positioned too close to each other
4. Elements positioned too close to the edge of the screen
5. Improper grouping of related elements
6. Elements with undefined positioning that might appear at origin (0,0)
7. Animations where multiple elements move to the same location

Analyze the coordinates and create a mental map of where objects are positioned.
Flag any positions where elements might overlap or be too close (less than 1.0 units apart).

Respond with a JSON object containing:
- positioning_issues: List of positioning problems found
- overlap_issues: List of specific coordinates or elements that might overlap
- suggestions: Specific suggestions to improve positioning
"""
            },
            {"role": "user", "content": f"Analyze this Manim code for positioning and spacing issues:\n\n```python\n{code}\n```\n\nPrompt: {prompt.description}, Complexity: {prompt.complexity}"}
        ]
    )
    
    content = response.choices[0].message.content
    
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            positioning_analysis = json.loads(json_str)
            return positioning_analysis
    except Exception as e:
        logger.error(f"Error parsing positioning analysis: {e}")
    
    # If no valid JSON is found, extract information manually
    positioning_issues = []
    overlap_issues = []
    suggestions = []
    
    # Simple pattern matching to extract issues
    for line in content.split('\n'):
        line = line.strip()
        if "position" in line.lower() or "coordinate" in line.lower() or "overlap" in line.lower():
            if line.startswith(("- ", "* ", "1. ", "2. ")):
                positioning_issues.append(line.lstrip("- *123456789. "))
        if "overlap" in line.lower():
            if line.startswith(("- ", "* ", "1. ", "2. ")):
                overlap_issues.append(line.lstrip("- *123456789. "))
        if "suggest" in line.lower() or "should" in line.lower() or "could" in line.lower():
            if line.startswith(("- ", "* ", "1. ", "2. ")):
                suggestions.append(line.lstrip("- *123456789. "))
    
    return {
        "positioning_issues": positioning_issues,
        "overlap_issues": overlap_issues,
        "suggestions": suggestions
    }

@evaluation_agent.tool
def fix_code_issues(ctx: RunContext[AnimationPrompt], code: str, syntax_errors: List[str], positioning_issues: dict) -> str:
    """Fix detected issues in the code."""
    prompt = ctx.deps
    
    # Format issues for the prompt
    syntax_errors_str = "\n".join([f"- {error}" for error in syntax_errors])
    
    positioning_issues_str = ""
    if "positioning_issues" in positioning_issues:
        positioning_issues_str += "\nPositioning Issues:\n" + "\n".join([f"- {issue}" for issue in positioning_issues["positioning_issues"]])
    
    if "overlap_issues" in positioning_issues:
        positioning_issues_str += "\nOverlap Issues:\n" + "\n".join([f"- {issue}" for issue in positioning_issues["overlap_issues"]])
    
    if "suggestions" in positioning_issues:
        positioning_issues_str += "\nSuggestions:\n" + "\n".join([f"- {suggestion}" for suggestion in positioning_issues["suggestions"]])
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Fix the provided Manim code by addressing all identified issues. Follow these guidelines:

1. Fix all syntax errors and logical mistakes first
2. Fix positioning issues by adding explicit positioning commands
3. Resolve element overlaps by repositioning elements with adequate spacing
4. Implement all positioning suggestions to improve clarity
5. Maintain the original educational intent and mathematical content
6. Ensure all animations follow a logical step-by-step flow
7. Add comments explaining your fixes for complex changes

Return the complete, corrected code ready for rendering.
"""
            },
            {"role": "user", "content": 
                f"Fix the following Manim code by addressing these issues:\n\n"
                f"Syntax Errors:\n{syntax_errors_str}\n\n"
                f"Positioning Issues:{positioning_issues_str}\n\n"
                f"Original Code:\n```python\n{code}\n```\n\n"
                f"Original Prompt: {prompt.description}, Complexity: {prompt.complexity}\n\n"
                f"Return the complete fixed code."
            }
        ]
    )
    
    fixed_code = response.choices[0].message.content
    
    # Clean up the response to extract just the code
    if "```python" in fixed_code:
        fixed_code = fixed_code.split("```python", 1)[1]
    if "```" in fixed_code:
        fixed_code = fixed_code.split("```", 1)[0]
    
    return fixed_code.strip()

@evaluation_agent.tool
def evaluate_code(ctx: RunContext[AnimationPrompt], code: str) -> EvaluationResult:
    """Evaluate Manim code for errors and positioning issues."""
    # Check for syntax errors
    syntax_errors = check_syntax_errors(ctx, code)
    
    # Check for positioning issues
    positioning_analysis = check_positioning(ctx, code)
    
    positioning_issues = positioning_analysis.get("positioning_issues", [])
    overlap_issues = positioning_analysis.get("overlap_issues", [])
    suggestions = positioning_analysis.get("suggestions", [])
    
    # Determine if there are errors
    has_errors = len(syntax_errors) > 0 or len(positioning_issues) > 0 or len(overlap_issues) > 0
    
    # If there are errors, fix the code
    fixed_code = None
    if has_errors:
        fixed_code = fix_code_issues(ctx, code, syntax_errors, positioning_analysis)
    
    return EvaluationResult(
        has_errors=has_errors,
        syntax_errors=syntax_errors,
        positioning_issues=positioning_issues,
        overlap_issues=overlap_issues,
        suggestions=suggestions,
        fixed_code=fixed_code
    )

@manim_agent.tool_plain
def render_animation(code: str, quality="medium_quality") -> str:
    """Render Manim code into a video. This doesn't need the context."""
    return render_manim_video(code, quality)

def render_manim_video(code, quality="medium_quality"):
    try:
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
        
        # Use a short random ID instead of the default long path from mkdtemp
        import uuid
        short_id = str(uuid.uuid4())[:8]  # Use only first 8 chars of UUID
        temp_dir = os.path.join(base_temp, short_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        script_path = os.path.join(temp_dir, "script.py")
        
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
        
        class_name = None
        for line in code.split("\n"):
            if line.startswith("class ") and "Scene" in line:
                class_name = line.split("class ")[1].split("(")[0].strip()
                break
            
        if not class_name:
            return "Error: Could not identify the Scene class in the generated code."
        
        if quality == "high_quality":
            command = ["manim", "-qh", script_path, class_name]
            quality_dir = "1080p60"
        elif quality == "low_quality":
            command = ["manim", "-ql", script_path, class_name]
            quality_dir = "480p15"
        else:
            command = ["manim", "-qm", script_path, class_name]
            quality_dir = "720p30"
        
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
        
        # Use a shorter filename format with timestamp
        from datetime import datetime
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

def format_log_output(scenario: AnimationScenario, code: str) -> str:
    """Format scenario and code for display in UI."""
    log_output = f"## Animation Scenario\n\n"
    log_output += f"**Title:** {scenario.title}\n\n"
    
    # Check if we have a storyboard in the logger
    import json
    import re
    from io import StringIO
    import logging
    
    # Create a string buffer to capture log output
    log_buffer = StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    logger.addHandler(log_handler)
    
    # Extract storyboard from logs if possible
    storyboard = None
    log_handler.flush()
    logs = log_buffer.getvalue()
    logger.removeHandler(log_handler)
    
    json_match = re.search(r'Generated storyboard: (\[.*\])', logs)
    if json_match:
        try:
            storyboard_str = json_match.group(1)
            storyboard = json.loads(storyboard_str)
        except:
            storyboard = None
    
    # If storyboard exists, display it
    if storyboard:
        log_output += f"## Animation Storyboard\n\n"
        for i, section in enumerate(storyboard):
            log_output += f"### {i+1}. {section.get('section_name', 'Section')}\n"
            log_output += f"**Time:** {section.get('time_range', 'N/A')}\n\n"
            log_output += f"**Narration:** {section.get('narration', '')}\n\n"
            log_output += f"**Visuals:** {section.get('visuals', '')}\n\n"
            log_output += f"**Animations:** {', '.join(section.get('animations', []))}\n\n"
            
            if 'key_points' in section and section['key_points']:
                log_output += f"**Key Points:**\n"
                if isinstance(section['key_points'], list):
                    for point in section['key_points']:
                        log_output += f"- {point}\n"
                else:
                    log_output += f"{section['key_points']}\n"
            
            log_output += "---\n\n"
    
    # Continue with regular output
    log_output += f"**Mathematical Objects:**\n"
    for obj in scenario.objects:
        log_output += f"- {obj}\n"
    
    log_output += f"\n**Transformations:**\n"
    for transform in scenario.transformations:
        log_output += f"- {transform}\n"
    
    if scenario.equations:
        log_output += f"\n**Equations:**\n"
        for eq in scenario.equations:
            log_output += f"- {eq}\n"
    
    log_output += f"\n## Generated Manim Code\n\n```python\n{code}\n```"
    
    return log_output

# Add a memory class to store conversation history
class ConversationMemory:
    def __init__(self):
        self.history = []
        self.current_scenario = None
        self.current_code = None
    
    def add_interaction(self, prompt, scenario, code, video_path):
        self.history.append({
            "prompt": prompt,
            "scenario": scenario,
            "code": code,
            "video_path": video_path,
            "timestamp": datetime.now().isoformat()
        })
        self.current_scenario = scenario
        self.current_code = code
    
    def get_context_for_refinement(self):
        if not self.history:
            return ""
        
        # Construct context from the last interaction
        last = self.history[-1]
        context = f"Previous prompt: {last['prompt']}\n"
        if self.current_scenario and hasattr(self.current_scenario, 'title'):
            context += f"Current animation title: {self.current_scenario.title}\n"
        return context

# Initialize the memory
memory = ConversationMemory()

# Function to refine animation based on feedback
def refine_animation(code: str, feedback: str, quality: str = "medium_quality") -> tuple:
    """Refine animation based on user feedback."""
    try:
        # Special case for layout/positioning feedback
        if any(keyword in feedback.lower() for keyword in ["position", "layout", "overlap", "spacing", "step by step", "clear"]):
            # Try to apply specialized layout optimization
            prompt = memory.history[-1]["prompt"] if memory.history else "Mathematical animation"
            complexity = "medium"  # Default complexity
            
            refined_code = optimize_element_positioning(code, prompt, complexity)
        else:
            # Original feedback processing code
            # Get context from memory
            context = memory.get_context_for_refinement()
            
            # Use LLM to refine the code based on feedback
            response = client.chat.completions.create(
                model=llm,
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
            # Update memory with refined code
            if memory.current_scenario:
                memory.current_code = refined_code
            
            return refined_code, video_path, f"## Refined Animation\n\nFeedback incorporated: \"{feedback}\"\n\nAnimation successfully rendered."
        else:
            return refined_code, None, f"## Error in Rendering\n\n```\n{video_path}\n```\n\nPlease check your code for errors."
    
    except Exception as e:
        logger.error(f"Error refining animation: {e}")
        return code, None, f"## Error in Refinement\n\n```\n{str(e)}\n```\n\nPlease try again with different feedback."

# Function to process user request
def generate_animation(prompt: str, complexity: str = "medium", quality: str = "medium_quality") -> tuple:
    """Generate an animation from a text prompt."""
    try:
        # Create prompt object with complexity
        prompt_obj = AnimationPrompt(description=prompt, complexity=complexity)
        
        # Run the agent in a way that it will use all necessary tools
        result = manim_agent.run_sync(
            f"Generate an animation from this description: {prompt}. "
            f"First, extract the key elements of the scenario. Then, generate "
            f"the Manim code for the animation. Finally, render the animation.",
            deps=prompt_obj
        )
        
        # As a fallback, we'll use the direct methods
        scenario = extract_scenario_direct(prompt, complexity)
        
        # Fix: Use generate_code_direct instead of generate_code
        # generate_code is an agent tool that requires a RunContext
        code = generate_code_direct(prompt, scenario, complexity)
        
        video_path = render_manim_video(code, quality)  # Use the new render function
        
        log_output = format_log_output(scenario, code)
        
        # Store in memory
        memory.add_interaction(prompt, scenario, code, video_path)
        
        return code, video_path, log_output
    except Exception as e:
        logger.error(f"Error generating animation: {e}")
        return f"Error: {str(e)}", None, f"Error occurred: {str(e)}"

# Add the missing generate_code_direct function if it doesn't exist
def generate_code_direct(prompt: str, scenario: AnimationScenario, complexity: str = "medium") -> str:
    """Direct implementation of code generation without using RunContext."""
    # Use Together API with OpenAI client
    objects_str = ", ".join(scenario.objects)
    transformations_str = ", ".join(scenario.transformations)
    equations_str = ", ".join(scenario.equations) if scenario.equations else "No equations"
    
    # Try to get storyboard from logger if it exists
    storyboard_info = ""
    from io import StringIO
    import re
    import json
    import logging
    
    # Create a string buffer to capture log output
    log_buffer = StringIO()
    log_handler = logging.StreamHandler(log_buffer)
    logger.addHandler(log_handler)
    log_handler.flush()
    logs = log_buffer.getvalue()
    logger.removeHandler(log_handler)
    
    # Extract storyboard from logs if possible
    json_match = re.search(r'Generated storyboard: (\[.*\])', logs)
    if json_match:
        try:
            storyboard_str = json_match.group(1)
            storyboard = json.loads(storyboard_str)
            storyboard_info = "Follow this narrative structure in your animation:\n"
            for i, section in enumerate(storyboard):
                storyboard_info += f"Section {i+1}: {section.get('section_name', 'Section')} - {section.get('time_range', 'N/A')}\n"
                storyboard_info += f"Narration: {section.get('narration', '')}\n"
                storyboard_info += f"Visuals: {section.get('visuals', '')}\n"
                storyboard_info += f"Animations: {', '.join(section.get('animations', []))}\n\n"
        except:
            storyboard_info = ""
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": f"""
Create professional Manim animation code that explains mathematical concepts clearly and elegantly. Your code MUST:

TECHNICAL REQUIREMENTS:
1. Use 'from manim import *' at the top
2. Create a Scene class named 'ManimScene' that extends Scene
3. Implement the construct method correctly
4. Use only standard Manim Community edition objects and methods
5. Include proper self.play() and self.wait() calls with appropriate durations
6. Use valid LaTeX syntax for all mathematical expressions
7. Be fully compilable without errors
8. Include helpful comments explaining each section
9. Just return python code, do not include apostrophe in front and back of code

VISUAL STRUCTURE AND LAYOUT:
1. Structure the animation as a narrative with clear sections (introduction, explanation, conclusion)
2. Create title screens with engaging typography and animations
3. Position ALL elements with EXPLICIT coordinates using shift() or move_to() methods
4. Ensure AT LEAST 2.0 units of space between separate visual elements
5. For equations, use MathTex with proper scaling (scale(0.8) for complex equations)
6. Group related objects using VGroup and arrange them with arrange() method
7. When showing multiple equations, use arrange_in_grid() or arrange() with DOWN/RIGHT
8. For graphs, set explicit x_range and y_range with generous padding around functions
9. Scale ALL text elements appropriately (Title: 1.2, Headers: 1.0, Body: 0.8)
10. Use colors consistently and meaningfully (BLUE for emphasis, RED for important points)

CRITICAL: ELEMENT MANAGEMENT AND STEP-BY-STEP REQUIREMENTS:
1. NEVER show too many elements on screen at once - max 3-4 related elements at any time
2. ALWAYS use self.play(FadeOut(element)) to explicitly remove elements when moving to a new concept
3. DO NOT use self.clear() as it doesn't actually remove elements from the scene
4. Implement strict SEQUENTIAL animation - introduce only ONE concept or element at a time
5. Use self.wait(0.7) to 1.5 for short pauses and self.wait(2) for important concepts
6. Organize the screen into distinct regions (TOP for titles, CENTER for main content, BOTTOM for explanations)
7. For sequential steps in derivations or proofs, use transform_matching_tex() to smoothly evolve equations
8. Use MoveToTarget() for repositioning elements that need to stay on screen between steps
9. At the end of each section, EXPLICITLY remove all elements with self.play(FadeOut(elem1, elem2, ...))
10. When positioning new elements, verify they won't overlap existing elements
11. For elements that must appear together, use VGroup but animate their creation one by one

ANIMATION TECHNIQUES:
1. Use FadeIn for introductions of new elements
2. Apply TransformMatchingTex when evolving equations
3. Use Create for drawing geometric objects
4. Implement smooth transitions between different concepts with ReplacementTransform
5. Highlight important parts with Indicate or Circumscribe
6. Add appropriate pauses: self.wait(0.7) after minor steps, self.wait(1.5) after important points
7. For complex animations, break them into smaller steps with appropriate timing
8. Use MoveAlongPath for demonstrating motion or change over time
9. Create emphasis with scale_about_point or succession of animations
10. Use camera movements sparingly and smoothly

EDUCATIONAL CLARITY:
1. Begin with simple concepts and build to more complex ones
2. Reveal information progressively, not all at once
3. Use visual metaphors to represent abstract concepts
4. Include clear labels for all important elements
5. When showing equations, animate their components step by step
6. Provide visual explanations alongside mathematical notation
7. Use consistent notation throughout the animation
8. Show practical applications or examples of the concept
9. Summarize key points at the end of the animation

{storyboard_info}

RESPOND WITH CLEAN, WELL-STRUCTURED CODE ONLY. DO NOT INCLUDE EXPLANATIONS OUTSIDE OF CODE COMMENTS.
"""
            },
            {"role": "user", "content": f"Create a comprehensive Manim animation for '{scenario.title}' that teaches this concept: '{prompt}'. \n\nUse these mathematical objects: {objects_str}. \nImplement these transformations/animations: {transformations_str}. \nFeature these equations: {equations_str}. \n\nComplexity level: {complexity}. \n\nEnsure all elements are properly spaced and positioned to prevent overlap. Structure the animation with a clear introduction, step-by-step explanation, and conclusion."}
        ]
    )
    
    initial_code = response.choices[0].message.content
    
    # Analyze and optimize the layout using the layout agent
    try:
        # Create prompt object for context
        prompt_obj = AnimationPrompt(description=prompt, complexity=complexity)
        
        # Fix: Don't pass 'code' as a keyword argument to run_sync
        # Instead, include the code in the prompt text
        layout_result = layout_agent.run_sync(
            f"Analyze and optimize the layout of this Manim code for the prompt: {prompt}\n\n"
            f"```python\n{initial_code}\n```",
            deps=prompt_obj
        )
        
        # If the layout agent successfully returned optimized code, use that
        if isinstance(layout_result, str) and "from manim import" in layout_result:
            # Extract the code part if it returned markdown-formatted code
            if "```python" in layout_result:
                layout_result = layout_result.split("```python", 1)[1].split("```", 1)[0].strip()
            return layout_result
        
        # Fix: Don't manually create a RunContext
        # Instead use a direct approach for optimization
        optimized_code = direct_optimize_layout(initial_code, prompt, complexity)
        
        if optimized_code and "from manim import" in optimized_code:
            return optimized_code
    except Exception as e:
        logger.error(f"Error during layout optimization: {e}")
        # If optimization fails, return the initial code
        
    return initial_code

# Add direct implementation of layout optimization functions
def direct_analyze_layout(code: str, prompt: str, complexity: str = "medium") -> dict:
    """Analyze Manim code for layout issues without using agent tools."""
    try:
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
                {"role": "user", "content": f"Analyze this Manim code for layout issues:\n\n```python\n{code}\n```\n\nPrompt: {prompt}, Complexity: {complexity}"}
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
    except Exception as e:
        logger.error(f"Error in direct_analyze_layout: {e}")
        return {
            "issues": ["Analysis failed"],
            "suggestions": ["Check code manually"],
            "animation_flow": [],
            "spacing": 1.0,
            "regions": ["CENTER"]
        }

def direct_optimize_layout(code: str, prompt: str, complexity: str = "medium") -> str:
    """Optimize layout in Manim code without using agent tools."""
    try:
        # First, analyze the layout
        analysis = direct_analyze_layout(code, prompt, complexity)
        
        # Serialize the analysis for the prompt
        analysis_str = json.dumps(analysis, indent=2)
        
        response = client.chat.completions.create(
            model=llm,
            messages=[
                {"role": "system", "content": """
Optimize the layout and animation flow in Manim code. Follow these strict rules:

ELEMENT POSITIONING AND SPACING:
1. Explicitly position ALL elements with coordinates (e.g., .move_to(), .shift(), .to_edge())
2. Ensure minimum spacing of 2.0 units between all elements
3. Use screen regions effectively (UP, DOWN, LEFT, RIGHT, UL, UR, DL, DR)
4. Group related elements using VGroup and arrange them with arrange(direction, buff=1.0)
5. Add buffer around elements: .move_to(point).shift(UP*0.5) to ensure spacing
6. Use coordinate grid to map element positions: x values from -6 to 6, y values from -3.5 to 3.5
7. Shrink elements to 80% size when needed with scale(0.8)

STEP-BY-STEP ANIMATION FLOW:
1. CRITICAL: Use self.play(FadeOut(element)) to explicitly remove elements when they're no longer needed
2. DO NOT use self.clear() as it doesn't actually remove elements from the scene
3. Divide the animation into clear sequences with comments like "# Step 1: Introduction"
4. Use appropriate wait times: self.wait(0.7) for minor steps, self.wait(1.5) for new concepts
5. At the end of each major section, add: self.play(FadeOut(*[all_objects_in_current_section]))
6. Max 3-4 elements should be visible simultaneously
7. For each step, state element positions clearly in comments
8. Use sequential animations (one element at a time) rather than AnimationGroup

FIXES FOR COMMON PROBLEMS:
1. Add .to_edge(direction) to all Tex/MathTex elements
2. For Title elements, always use .to_edge(UP)
3. For equations, use .scale(0.8).next_to(previous_element, DOWN*2)
4. For diagrams, center them with .move_to(ORIGIN)
5. For graphs, explicitly set axes ranges with x_range=[-5, 5, 1], y_range=[-3, 3, 1]
6. For multiple text elements, align them with .align_to(reference, direction)
7. For explanatory text, position at the bottom with .to_edge(DOWN)
8. Before introducing new sections, add: self.play(FadeOut(*[all_current_elements]))

Preserve all mathematical content and educational purpose of the animation.
Only make changes to improve layout, positioning, and animation flow.
"""
                },
                {"role": "user", "content": f"Original code:\n\n```python\n{code}\n```\n\nOptimize the layout based on this analysis:\n{analysis_str}\n\nPrompt: {prompt}, Complexity: {complexity}\n\nReturn the optimized code that ensures a step-by-step animation with proper spacing and element removal to prevent overlaps."}
            ]
        )
        
        optimized_code = response.choices[0].message.content
        
        # Clean up the response to extract just the code
        if "```python" in optimized_code:
            optimized_code = optimized_code.split("```python", 1)[1]
        if "```" in optimized_code:
            optimized_code = optimized_code.split("```", 1)[0]
        
        return optimized_code.strip()
    except Exception as e:
        logger.error(f"Error in direct_optimize_layout: {e}")
        return code  # Return original code if optimization fails

# Add a new function to specifically check and fix positioning issues in existing code
def optimize_element_positioning(code: str, prompt: str, complexity: str = "medium") -> str:
    """Analyze and optimize element positioning in Manim code."""
    try:
        response = client.chat.completions.create(
            model=llm,
            messages=[
                {"role": "system", "content": """
You are a Manim layout expert. Review the provided code and improve element positioning and animation flow.
Focus on these critical aspects:

1. STEP-BY-STEP ANIMATION:
   - CRITICAL: Add explicit self.play(FadeOut(...)) to remove elements when they're no longer needed
   - DO NOT use self.clear() as it doesn't actually remove elements from the scene
   - Ensure only 3-4 related elements are visible at once
   - Sequence animations to show just one new element at a time
   - Use appropriate wait times: self.wait(0.7) for minor points, self.wait(1.5) for important concepts

2. POSITIONING AND SPACING:
   - Position ALL elements with explicit coordinates: move_to(), shift(), to_edge(), etc.
   - Maintain AT LEAST 2.0 units of space between elements
   - Use all screen regions effectively: UP, DOWN, LEFT, RIGHT, UL, UR, DL, DR, etc.
   - Use coordinate grid system: x values from -6 to 6, y values from -3.5 to 3.5
   - Scale elements with .scale(0.8) when needed to prevent overlap

3. ELEMENT ORGANIZATION:
   - Group related elements using VGroup and arrange them with arrange(direction, buff=1.0)
   - Position titles at the top with .to_edge(UP)
   - Position explanatory text at the bottom with .to_edge(DOWN)
   - Center diagrams with .move_to(ORIGIN)
   - For multiple text elements, use .align_to(reference, direction)

4. ELEMENT CLEANUP:
   - At the end of each section, add: self.play(FadeOut(*[all_objects_in_section]))
   - For elements that transform, use ReplacementTransform not Transform
   - Keep track of all created elements and remove them when not needed
   - Add comments before element removal: "# Remove all elements from this section"

DO NOT change the mathematical content or educational purpose of the animation.
Only modify layout, positioning, and animation flow to ensure a clear, step-by-step experience.

Return ONLY the improved code without explanations outside of code comments.
"""
                },
                {"role": "user", "content": f"Review and optimize element positioning and step-by-step flow in this Manim code:\n\n```python\n{code}\n```\n\nThe animation is about: '{prompt}' with complexity level '{complexity}'.\n\nFocus on preventing element overlap by ensuring proper spacing, explicit positioning, AND ADDING FadeOut() calls to remove elements when moving between sections. DO NOT use self.clear() since it doesn't work properly."}
            ]
        )
        
        optimized_code = response.choices[0].message.content
        
        # Clean up the response to extract just the code
        if "```python" in optimized_code:
            optimized_code = optimized_code.split("```python", 1)[1]
        if "```" in optimized_code:
            optimized_code = optimized_code.split("```", 1)[0]
        
        return optimized_code.strip()
    except Exception as e:
        logger.error(f"Error optimizing element positioning: {e}")
        return code  # Return original code if optimization fails

# Function to re-render animation with edited code
def rerender_animation(edited_code: str, quality: str = "medium_quality") -> tuple:
    """Re-render animation with user-edited code."""
    try:
        video_path = render_manim_video(edited_code, quality)
        if video_path and not video_path.startswith("Error"):
            return video_path, f"## Re-rendered Animation\n\nCode successfully rendered to video.\n\nCheck the video player for results."
        else:
            return None, f"## Error in Rendering\n\n```\n{video_path}\n```\n\nPlease check your code for errors."
    except Exception as e:
        logger.error(f"Error re-rendering animation: {e}")
        return None, f"## Error in Rendering\n\n```\n{str(e)}\n```\n\nPlease check your code for errors."

# Setup Gradio interface
def gradio_interface(prompt: str, complexity: str = "medium", quality: str = "medium_quality"):
    code, video_path, log_output = generate_animation(prompt, complexity, quality)
    if video_path and not video_path.startswith("Error"):
        return code, video_path, log_output
    else:
        return code, None, log_output

# Function to evaluate and fix Manim code
def evaluate_and_fix_manim_code(code: str, prompt: str, complexity: str = "medium") -> tuple:
    """Evaluate Manim code for errors and fix them if found."""
    try:
        # Create prompt object for context
        prompt_obj = AnimationPrompt(description=prompt, complexity=complexity)
        
        # Run evaluation through the agent
        evaluation_result = evaluation_agent.run_sync(
            f"Evaluate this Manim code for the prompt: {prompt}",
            deps=prompt_obj,
            code=code
        )
        
        # Check if we got a proper evaluation result
        if isinstance(evaluation_result, EvaluationResult):
            if evaluation_result.has_errors and evaluation_result.fixed_code:
                return evaluation_result.fixed_code, format_evaluation_results(evaluation_result)
            elif evaluation_result.has_errors:
                # If no fixed code was provided but errors exist, try direct fixing
                prompt_ctx = RunContext(deps=prompt_obj)
                fixed_code = fix_code_issues(
                    prompt_ctx, 
                    code, 
                    evaluation_result.syntax_errors,
                    {
                        "positioning_issues": evaluation_result.positioning_issues,
                        "overlap_issues": evaluation_result.overlap_issues,
                        "suggestions": evaluation_result.suggestions
                    }
                )
                return fixed_code, format_evaluation_results(evaluation_result)
            else:
                # No errors found
                return code, "## Code Evaluation\n\nNo errors or positioning issues found. Code looks good!"
        
        # Fallback to direct evaluation if agent result isn't an EvaluationResult
        return direct_evaluate_and_fix(code, prompt, complexity)
    
    except Exception as e:
        logger.error(f"Error during code evaluation: {e}")
        # If evaluation fails, return the original code
        return code, f"## Error During Evaluation\n\nCould not complete code evaluation: {str(e)}"

def direct_evaluate_and_fix(code: str, prompt: str, complexity: str = "medium") -> tuple:
    """Direct implementation of code evaluation and fixing without using agents."""
    try:
        response = client.chat.completions.create(
            model=llm,
            messages=[
                {"role": "system", "content": """
Evaluate this Manim code for errors and positioning issues. Look for:
1. Python syntax errors
2. Manim-specific errors (incorrect class usage, invalid animation methods)
3. Positioning issues (elements without explicit positioning)
4. Potential element overlaps
5. Timing and animation flow issues

If you find any issues, fix them and return both an evaluation report and the fixed code.
If no issues are found, say so and return the original code.

Format your response as:
```evaluation
[List all issues found with explanations]
```

```python
[The fixed code or original code if no issues]
```
"""
                },
                {"role": "user", "content": f"Evaluate this Manim code:\n\n```python\n{code}\n```\n\nThe animation is about: '{prompt}' with complexity level '{complexity}'.\n\nCheck for errors and positioning issues, especially element overlaps."}
            ]
        )
        
        content = response.choices[0].message.content
        
        # Extract evaluation report
        evaluation_report = ""
        if "```evaluation" in content:
            evaluation_parts = content.split("```evaluation", 1)[1].split("```", 1)
            if len(evaluation_parts) > 0:
                evaluation_report = evaluation_parts[0].strip()
        
        # Extract fixed code
        fixed_code = code  # Default to original code
        if "```python" in content:
            code_parts = content.split("```python", 1)[1].split("```", 1)
            if len(code_parts) > 0:
                potential_fixed_code = code_parts[0].strip()
                # Only use the fixed code if it's valid (contains basic Manim imports)
                if "from manim import" in potential_fixed_code or "import manim" in potential_fixed_code:
                    fixed_code = potential_fixed_code
        
        # Format the evaluation report
        if evaluation_report:
            formatted_report = f"## Code Evaluation\n\n{evaluation_report}\n\n"
            if fixed_code != code:
                formatted_report += "Issues were found and fixed in the code."
            return fixed_code, formatted_report
        else:
            return fixed_code, "## Code Evaluation\n\nNo significant issues found in the code."
    
    except Exception as e:
        logger.error(f"Error during direct evaluation: {e}")
        return code, f"## Error During Evaluation\n\nCould not complete code evaluation: {str(e)}"

def format_evaluation_results(result: EvaluationResult) -> str:
    """Format evaluation results for display."""
    output = "## Code Evaluation Results\n\n"
    
    if not result.has_errors:
        output += "✅ No errors or positioning issues detected. Code looks good!\n\n"
        return output
    
    if result.syntax_errors:
        output += "### Syntax Errors\n\n"
        for i, error in enumerate(result.syntax_errors):
            output += f"{i+1}. {error}\n"
        output += "\n"
    
    if result.positioning_issues:
        output += "### Positioning Issues\n\n"
        for i, issue in enumerate(result.positioning_issues):
            output += f"{i+1}. {issue}\n"
        output += "\n"
    
    if result.overlap_issues:
        output += "### Potential Element Overlaps\n\n"
        for i, issue in enumerate(result.overlap_issues):
            output += f"{i+1}. {issue}\n"
        output += "\n"
    
    if result.suggestions:
        output += "### Suggestions for Improvement\n\n"
        for i, suggestion in enumerate(result.suggestions):
            output += f"{i+1}. {suggestion}\n"
        output += "\n"
    
    if result.fixed_code:
        output += "✅ These issues have been automatically fixed in the updated code.\n"
    else:
        output += "❌ Could not automatically fix all issues. Please review the code manually.\n"
    
    return output

# Replace the Gradio interface creation with a Blocks interface for better layout control
if __name__ == "__main__":
    # Create shorter directory names for temp and output files
    # Check if we're running on Hugging Face
    is_huggingface = os.environ.get("SPACE_ID") is not None
    
    # Use appropriate directories based on environment
    if is_huggingface:
        # Use /tmp directory for HF Spaces which has write permissions
        os.makedirs("/tmp/videos", exist_ok=True)
    else:
        os.makedirs(os.path.join(os.getcwd(), "tmp"), exist_ok=True)
        os.makedirs(os.path.join(os.getcwd(), "videos"), exist_ok=True)
    
    with gr.Blocks(title="Manimation Generator", theme=gr.themes.Base()) as demo:
        gr.Markdown("# Manimation Generator")
        gr.Markdown("Generate mathematical animations from text descriptions using AI")
        
        # Add chat history component
        chat_history = gr.Chatbot(label="Conversation History", height=300)
        
        with gr.Row():
            # Left column: User inputs
            with gr.Column(scale=1):
                # Replace single prompt with tabs for initial creation and feedback
                with gr.Tabs():
                    with gr.TabItem("Create New Animation"):
                        new_prompt = gr.Textbox(
                            lines=5, 
                            placeholder="Describe a mathematical concept to animate...", 
                            label="Concept Description"
                        )
                        
                        with gr.Row():
                            complexity = gr.Radio(
                                ["simple", "medium", "complex"], 
                                value="medium", 
                                label="Complexity Level"
                            )
                            quality = gr.Radio(
                                ["low_quality", "medium_quality", "high_quality"], 
                                value="medium_quality", 
                                label="Video Quality"
                            )
                        
                        generate_btn = gr.Button("Generate Animation", variant="primary")
                    
                    with gr.TabItem("Refine Animation"):
                        feedback = gr.Textbox(
                            lines=3,
                            placeholder="Provide feedback or suggestions for the current animation...",
                            label="Your Feedback"
                        )
                        refine_btn = gr.Button("Apply Feedback", variant="secondary")
                    
                    # Add the missing "Evaluate Code" tab
                    with gr.TabItem("Evaluate Code"):
                        gr.Markdown("""
                        Check your Manim code for:
                        - Syntax errors
                        - Positioning issues
                        - Element overlaps
                        - Animation flow problems
                        """)
                        evaluate_btn = gr.Button("Check Code for Errors", variant="secondary")
                
                # Code editor (common to both tabs)
                code_output = gr.Code(
                    language="python", 
                    label="Manim Code (Editable)",
                    lines=20,
                    interactive=True
                )
                
                # Add manual rerender button
                rerender_btn = gr.Button("Re-render Current Code", variant="secondary")
            
            # Right column: Video and details
            with gr.Column(scale=1):
                video_output = gr.Video(label="Animation")
                # Uncomment the log_output component to fix the error
                log_output = gr.Markdown(label="Details")
        
        # Function to update chat history
        def update_chat_history(history, user_message, bot_message, video_path):
            history = history or []
            history.append((user_message, None))  # User message
            if video_path and not isinstance(video_path, str):
                # If we have a valid video, include it in the message
                bot_message = f"{bot_message}\n\n![Animation]({video_path})"
            history.append((None, bot_message))  # Bot message
            return history
        
        # Function wrappers for UI updates with chat history
        def generate_and_update_chat(prompt, complexity, quality, history):
            code, video_path, log = generate_animation(prompt, complexity, quality)
            new_history = update_chat_history(
                history, 
                f"**Create animation:** {prompt}",
                f"**Generated animation:** {memory.current_scenario.title if memory.current_scenario else 'Animation'}", 
                video_path
            )
            return code, video_path, log, new_history
        
        def refine_and_update_chat(code, feedback_text, quality, history):
            refined_code, video_path, log = refine_animation(code, feedback_text, quality)
            new_history = update_chat_history(
                history, 
                f"**Feedback:** {feedback_text}", 
                f"**Refined animation based on feedback**", 
                video_path
            )
            return refined_code, video_path, log, new_history
        
        def rerender_and_update_chat(code, quality, history):
            video_path, log = rerender_animation(code, quality)
            new_history = update_chat_history(
                history, 
                "**Re-rendered current code**", 
                "**Re-rendering complete**", 
                video_path
            )
            return video_path, log, new_history
        
        def evaluate_and_update_chat(code, history):
            # Extract prompt from memory
            prompt = memory.history[-1]["prompt"] if memory.history else "Mathematical animation"
            complexity = "medium"  # Default complexity
            
            # Evaluate the code
            fixed_code, evaluation_report = evaluate_and_fix_manim_code(code, prompt, complexity)
            
            new_history = update_chat_history(
                history, 
                "**Request:** Check code for errors and positioning issues", 
                f"**Evaluation complete**", 
                None
            )
            
            return fixed_code, evaluation_report, new_history
        
        # Connect the components to the function
        generate_btn.click(
            fn=generate_and_update_chat,
            inputs=[new_prompt, complexity, quality, chat_history],
            outputs=[code_output, video_output, log_output, chat_history]
        )
        
        refine_btn.click(
            fn=refine_and_update_chat,
            inputs=[code_output, feedback, quality, chat_history],
            outputs=[code_output, video_output, log_output, chat_history]
        )
        
        rerender_btn.click(
            fn=rerender_and_update_chat,
            inputs=[code_output, quality, chat_history],
            outputs=[video_output, log_output, chat_history]
        )
        
        evaluate_btn.click(
            fn=evaluate_and_update_chat,
            inputs=[code_output, chat_history],
            outputs=[code_output, log_output, chat_history]
        )
        
        # Add footer with social media links
        with gr.Row(equal_height=True):
            gr.Markdown("""
                ### Connect With Us
                
                [<img src="https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png" width="30"/> GitHub](https://github.com/khanhthanhdev/Text2Video) | 
                [<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Facebook_Logo_%282019%29.png/600px-Facebook_Logo_%282019%29.png" width="30"/> Facebook](https://facebook.com/khanhthanhdev)
                
                ---
                *Created with Manim and AI - Share your mathematical animations with the world!*
            """)
    
    demo.launch(server_name="0.0.0.0", server_port=7860)


