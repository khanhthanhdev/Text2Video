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

@manim_agent.tool
def extract_scenario(ctx: RunContext[AnimationPrompt]) -> AnimationScenario:
    """Extract a structured animation scenario from a text prompt."""
    prompt = ctx.deps  # Get the AnimationPrompt from context
    
    # Use Together API with OpenAI client
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": "Extract structured information for a mathematical animation."},
            {"role": "user", "content": f"From this description: '{prompt.description}', extract the title, "
                                        f"mathematical objects, transformations, and equations. "
                                        f"Consider complexity level: {prompt.complexity}."}
        ]
    )
    content = response.choices[0].message.content
    
    # Parse the response into structured data
    # This is simplified; in reality, you would need more robust parsing
    scenario_dict = {
        "title": "Generated Animation",
        "objects": ["circle", "line"],
        "transformations": ["rotation"],
        "equations": None
    }
    return AnimationScenario(**scenario_dict)

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

def render_manim_video(code, quality="medium_quality"):
    try:
        temp_dir = tempfile.mkdtemp()
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
        
        output_dir = os.path.join(os.getcwd(), "generated_videos")
        os.makedirs(output_dir, exist_ok=True)
        
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

def format_log_output(scenario: AnimationScenario, code: str) -> str:
    """Format scenario and code for display in UI."""
    log_output = f"## Animation Scenario\n\n"
    log_output += f"**Title:** {scenario.title}\n\n"
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

# Function to process user request
def generate_animation(prompt: str, complexity: str = "medium", quality: str = "medium_quality") -> tuple:
    """Generate an animation from a text prompt."""
    try:
        # Create prompt object with complexity
        prompt_obj = AnimationPrompt(description=prompt, complexity=complexity)
        
        # Run the agent in a way that it will use all necessary tools
        result = manim_agent.run_sync(
            f"Create a Manim animation based on this description: {prompt}. "
            f"First, extract the key elements of the scenario. Then, generate "
            f"Manim code for the animation. Finally, render the animation.",
            deps=prompt_obj
        )
        
        # Direct implementation as a fallback
        scenario = extract_scenario_direct(prompt, complexity)
        code = generate_code_direct(prompt, scenario, complexity)
        video_path = render_manim_video(code, quality)  # Use the new render function
        
        log_output = format_log_output(scenario, code)
        
        return code, video_path, log_output
    except Exception as e:
        logger.error(f"Error generating animation: {e}")
        return f"Error: {str(e)}", None, f"Error occurred: {str(e)}"

def extract_scenario_direct(prompt: str, complexity: str = "medium") -> AnimationScenario:
    """Direct implementation of scenario extraction without using RunContext."""
    # Use Together API with OpenAI client
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Create a detailed storyboard for a mathematical or physics concept animation. The storyboard should follow a narrative structure with clear sections and timestamps. Think of this as a script for an educational video.

Respond with a JSON object containing:
- title: A descriptive and engaging title for the animation
- objects: An array of mathematical objects to be used (e.g., "coordinate_plane", "function_graph", "integral_symbol")
- transformations: An array of transformations/animations (e.g., "fade_in", "transform", "highlight")
- equations: An array of mathematical equations to feature (can be null if none)
- storyboard: An array of sections, each with:
  * section_name: Name of this section (e.g., "Introduction", "Concept Explanation")
  * time_range: Approximate timestamp range (e.g., "0:00-1:30")
  * narration: What the narrator would say during this section
  * visuals: Description of what should be shown visually
  * animations: Specific animations to perform in this section

Example response:
{
  "title": "Understanding Integrals: A Visual Journey",
  "objects": ["coordinate_plane", "curve_function", "rectangles", "integral_symbol"],
  "transformations": ["fade_in", "rectangle_approximation", "limit_process"],
  "equations": ["∫(a,b) f(x) dx", "F(b) - F(a)"],
  "storyboard": [
    {
      "section_name": "Introduction",
      "time_range": "0:00-1:00",
      "narration": "Integrals might seem intimidating at first, but they're actually a powerful tool for measuring areas.",
      "visuals": "Title screen with 'Understanding Integrals' text, mathematical symbols flowing into view",
      "animations": ["fade_in_title", "animate_symbols"]
    },
    {
      "section_name": "The Problem of Area",
      "time_range": "1:00-3:00",
      "narration": "Imagine we want to find the area under this curve. For regular shapes, we have simple formulas, but what about irregular shapes?",
      "visuals": "A quadratic function like y = x² on a coordinate plane with highlighted region underneath",
      "animations": ["draw_coordinate_plane", "plot_function", "highlight_region"]
    }
  ]
}

CREATE A COMPLETE STORYBOARD with 5-7 sections that logically explain the concept. Include an introduction, step-by-step explanation of the concept, and conclusion/applications. Make sure the narration is educational, clear, and builds understanding progressively.

Only respond with the JSON object, nothing else.
"""
            },
            {"role": "user", "content": f"Create a detailed animation storyboard for this concept: '{prompt}'. "
                                        f"Consider complexity level: {complexity}. "
                                        f"Include a clear introduction, step-by-step explanations with visual descriptions, "
                                        f"and practical applications or conclusion."}
        ]
    )
    content = response.choices[0].message.content
    
    # Parse the response into structured data
    try:
        # Try to extract JSON from the response
        import json
        import re
        
        # Look for JSON pattern in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            scenario_dict = json.loads(json_str)
            
            # Extract the basic scenario info we need for the AnimationScenario model
            title = scenario_dict.get('title', f"{prompt.capitalize()} Visualization")
            objects = scenario_dict.get('objects', [])
            transformations = scenario_dict.get('transformations', [])
            equations = scenario_dict.get('equations', None)
            
            # Store the full storyboard in the logger for reference
            if 'storyboard' in scenario_dict:
                logger.info(f"Generated storyboard: {json.dumps(scenario_dict['storyboard'], indent=2)}")
            
            # Return the AnimationScenario with the basic info
            return AnimationScenario(
                title=title,
                objects=objects,
                transformations=transformations,
                equations=equations
            )
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        logger.error(f"Error parsing scenario JSON: {e}")
    
    # Fallback with default values if parsing fails
    scenario_dict = {
        "title": f"{prompt.capitalize()} Visualization",
        "objects": ["circle", "line", "text"],
        "transformations": ["creation", "movement"],
        "equations": None
    }
    
    # Extract some likely objects based on common keywords in the prompt
    if any(kw in prompt.lower() for kw in ["triangle", "pythagorean"]):
        scenario_dict["objects"] = ["triangle", "square", "text"]
        scenario_dict["transformations"] = ["creation", "area_calculation"]
        scenario_dict["equations"] = ["a^2 + b^2 = c^2"]
    elif any(kw in prompt.lower() for kw in ["circle", "sphere"]):
        scenario_dict["objects"] = ["circle", "radius_line", "label"]
        scenario_dict["transformations"] = ["drawing", "scaling"]
    elif any(kw in prompt.lower() for kw in ["function", "graph", "plot"]):
        scenario_dict["objects"] = ["axes", "graph", "tangent_line"]
        scenario_dict["transformations"] = ["plotting", "highlighting"]
    elif any(kw in prompt.lower() for kw in ["vector", "force"]):
        scenario_dict["objects"] = ["vector", "point", "line"]
        scenario_dict["transformations"] = ["translation", "rotation"]
        
    return AnimationScenario(**scenario_dict)

def generate_code_direct(prompt: str, scenario: AnimationScenario, complexity: str = "medium") -> str:
    """Direct implementation of code generation without using RunContext."""
    # Use Together API with OpenAI client
    objects_str = ", ".join(scenario.objects)
    transformations_str = ", ".join(scenario.transformations)
    equations_str = ", ".join(scenario.equations) if scenario.equations else "No equations"
    
    # Try to get storyboard from logger if it exists
    storyboard_info = ""

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
4. Ensure AT LEAST 1.5 units of space between separate visual elements
5. For equations, use MathTex with proper scaling (scale(0.8) for complex equations)
6. Group related objects using VGroup and arrange them with arrange() method
7. When showing multiple equations, use arrange_in_grid() or arrange() with DOWN/RIGHT
8. For graphs, set explicit x_range and y_range with generous padding around functions
9. Scale ALL text elements appropriately (Title: 1.2, Headers: 1.0, Body: 0.8)
10. Use colors consistently and meaningfully (BLUE for emphasis, RED for important points)
11. Preventing overlaps of element, choose position for each element carefully, display element and text then move to next element
             
ANIMATION TECHNIQUES:
1. Use FadeIn for introductions of new elements
2. Apply TransformMatchingTex when evolving equations
3. Use Create for drawing geometric objects
4. Implement smooth transitions between different concepts with ReplacementTransform
5. Highlight important parts with Indicate or Circumscribe
6. Add pauses (self.wait()) after important points for comprehension
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
    return response.choices[0].message.content

# Setup Gradio interface
def gradio_interface(prompt: str, complexity: str = "medium", quality: str = "medium_quality"):
    code, video_path, log_output = generate_animation(prompt, complexity, quality)
    if video_path and not video_path.startswith("Error"):
        return code, video_path, log_output
    else:
        return code, None, log_output

# Replace the Gradio interface creation with a Blocks interface for better layout control
if __name__ == "__main__":
    with gr.Blocks(title="Manimation Generator", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# Manimation Generator")
        gr.Markdown("Generate mathematical animations from text descriptions using AI")
        
        with gr.Row():
            # Left column: User inputs and code
            with gr.Column(scale=1):
                prompt = gr.Textbox(
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
                
                code_output = gr.Code(
                    language="python", 
                    label="Generated Manim Code", 
                    lines=20
                )
            
            # Right column: Video and scenario details
            with gr.Column(scale=1):
                video_output = gr.Video(label="Generated Animation")
                log_output = gr.Markdown(label="Animation Details")
        
        # Connect the components to the function
        generate_btn.click(
            fn=gradio_interface,
            inputs=[prompt, complexity, quality],
            outputs=[code_output, video_output, log_output]
        )
    
    demo.launch()

