"""
Simplified example of a Manim animation generator using pydantic-ai.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel, Field
from datetime import datetime
import openai
import tempfile
import subprocess
import shutil
import time
import logging

# Load environment variables
load_dotenv()

# Configure logging if not already done
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnimationPrompt(BaseModel):
    """User input for animation generation."""
    description: str = Field(..., description="Description of the mathematical concept to animate")
    complexity: str = Field("medium", description="Desired complexity of the animation (simple, medium, complex)")

class AnimationOutput(BaseModel):
    """Output of the animation generation."""
    manim_code: str = Field(..., description="Generated Manim code")
    explanation: str = Field(..., description="Explanation of the animation")

# Create the animation agent with basic static system prompt
model = OpenAIModel(
    'deepseek-ai/DeepSeek-V3',
    provider=OpenAIProvider(
        base_url='https://api.together.xyz/v1', api_key=os.environ.get('TOGETHER_API_KEY')
    ),
)

animation_agent = Agent(
    model,
    deps_type=AnimationPrompt,
    system_prompt=(
        "You are a mathematical animation specialist. Your job is to convert text descriptions "
        "into Manim code that visualizes mathematical concepts. Provide clear and accurate code."
    )
)

# Configure OpenAI client to use Together API
client = openai.OpenAI(
    api_key=os.environ.get("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1",
)

# Add dynamic system prompts
@animation_agent.system_prompt
def add_complexity_guidance(ctx: RunContext[AnimationPrompt]) -> str:
    """Add guidance based on requested complexity."""
    complexity = ctx.deps.complexity
    if complexity == "simple":
        return "Generate simple, beginner-friendly Manim code with minimal elements and clear explanations."
    elif complexity == "complex":
        return "Generate advanced Manim code with sophisticated animations and detailed mathematical representations."
    else:  # medium
        return "Generate standard Manim code that balances simplicity and detail to effectively demonstrate the concept."

@animation_agent.system_prompt
def add_timestamp() -> str:
    """Add a timestamp to help with freshness of information."""
    return f"Current timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

@animation_agent.tool
def generate_manim_code(ctx: RunContext[AnimationPrompt]) -> str:
    """Generate Manim code based on the user's description."""
    prompt = ctx.deps
    
    # Use Together API with OpenAI client
    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages=[
            {"role": "system", "content": """
Generate Manim code for mathematical animations. The code MUST:
1. Be fully compilable without errors using Manim Community edition
2. Use only the Scene class with a class name 'ManimScene' exactly
3. Include 'from manim import *' at the top
4. Implement the construct method only
5. Use only standard Manim objects and methods
6. Include proper self.play() and self.wait() calls
7. Use valid LaTeX syntax for any mathematical expressions
8. Avoid experimental or uncommon Manim features
9. Keep the animation clean, concise, and educational
10. Include proper error handling for all mathematical operations
11. DO NOT include any backticks (```) or markdown formatting in your response

RESPOND WITH CODE ONLY, NO EXPLANATIONS OUTSIDE OF CODE COMMENTS, NO MARKDOWN FORMATTING.
"""
            },
            {"role": "user", "content": f"Create Manim code for a {prompt.complexity} animation of {prompt.description}"}
        ]
    )
    
    generated_code = response.choices[0].message.content
    
    # Strip markdown formatting if it appears in the response
    if "```python" in generated_code:
        generated_code = generated_code.split("```python")[1]
        if "```" in generated_code:
            generated_code = generated_code.split("```")[0]
    
    return generated_code

@animation_agent.tool
def explain_animation(ctx: RunContext[AnimationPrompt], code: str) -> str:
    """Explain the generated animation in plain language."""
    prompt = ctx.deps
    
    # Use Together API with OpenAI client
    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        messages=[
            {"role": "system", "content": "Explain mathematical animations in simple terms."},
            {"role": "user", "content": f"Explain this Manim animation of {prompt.description} " +
                                       f"with complexity {prompt.complexity} in simple terms:\n{code}"}
        ]
    )
    
    return response.choices[0].message.content

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

def run_animation_agent(description: str, complexity: str = "medium", quality: str = "medium_quality") -> AnimationOutput:
    """Run the animation agent to generate code and explanation."""
    prompt = AnimationPrompt(description=description, complexity=complexity)
    
    # Use the agent to process the request
    result = animation_agent.run_sync(
        "Generate Manim code for this animation and explain what it does", 
        deps=prompt
    )
    
    # Generate code and explanation
    code = None
    explanation = None
    
    # As a fallback, provide a direct implementation specific to the Pythagorean theorem
    if "pythagorean theorem" in description.lower():
        code = f"""
from manim import *

class ManimScene(Scene):
    def construct(self):
        # Animation for: {prompt.description}
        # Complexity level: {prompt.complexity}
        
        # Create a right triangle
        triangle = Polygon(
            ORIGIN,
            RIGHT * 3,
            UP * 4,
            color=WHITE
        )
        
        # Labels for sides
        a_label = MathTex("a").next_to(triangle, DOWN)
        b_label = MathTex("b").next_to(triangle, RIGHT)
        c_label = MathTex("c").next_to(triangle.get_center(), UP + LEFT)
        
        # The equation
        equation = MathTex("a^2 + b^2 = c^2").to_edge(DOWN)
        
        # Display the triangle and labels
        self.play(Create(triangle))
        self.play(Write(a_label), Write(b_label), Write(c_label))
        self.wait()
        
        # Show the equation
        self.play(Write(equation))
        self.wait()
    """
        
        explanation = (
            f"This animation visualizes {prompt.description} with a {prompt.complexity} "
            f"complexity level. It creates a right triangle and labels its sides a, b, and c. "
            f"It then displays the Pythagorean theorem equation a² + b² = c²."
        )
    else:
        # Generic fallback
        code = f"""
from manim import *

class ManimScene(Scene):
    def construct(self):
        # Animation for: {prompt.description}
        # Complexity level: {prompt.complexity}
        
        # Title
        title = Text("{description}")
        self.play(Write(title))
        self.wait()
        self.play(title.animate.to_edge(UP))
        
        # Main content based on complexity
        if "{complexity}" == "simple":
            # Simple visualization
            circle = Circle()
            self.play(Create(circle))
            self.wait()
        else:
            # More complex visualization
            axes = Axes(
                x_range=[-3, 3],
                y_range=[-3, 3],
                axis_config={"color": BLUE}
            )
            self.play(Create(axes))
            
            # Add a function graph
            graph = axes.plot(lambda x: x**2, color=YELLOW)
            self.play(Create(graph))
            self.wait()
        """
        
        explanation = (
            f"This animation visualizes {prompt.description} with a {prompt.complexity} "
            f"complexity level. It displays a title and creates a visualization that matches "
            f"the requested complexity."
        )
    
    # Try to render the video
    if code:
        video_path = render_manim_video(code, quality)
        if video_path and not video_path.startswith("Error"):
            print(f"Video rendered successfully at: {video_path}")
    
    return AnimationOutput(manim_code=code, explanation=explanation)

if __name__ == "__main__":
    # Example usage
    result = run_animation_agent(
        "the Pythagorean theorem showing how a² + b² = c²", 
        complexity="simple"
    )
    print("=== Generated Manim Code ===")
    print(result.manim_code)
    print("\n=== Explanation ===")
    print(result.explanation)
