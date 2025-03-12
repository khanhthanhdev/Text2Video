import gradio as gr
import os
import tempfile
import subprocess
import shutil
import logging
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_client():
    return OpenAI(
        api_key=os.environ.get("TOGETHER_API_KEY"),
        base_url="https://api.together.xyz/v1"
    )

AVAILABLE_MODELS = [
    "meta-llama/Llama-3.3-70B-Instruct-Turbo",
    "deepseek-ai/DeepSeek-V3",
    "deepseek-ai/DeepSeek-R1",
    "Qwen/QwQ-32B-Preview",
    "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    "Qwen/Qwen2.5-Coder-32B-Instruct"
]

def generate_manim_code(prompt, model_name, temperature=0.7, max_tokens=8192):
    try:
        client = get_client()
        system_prompt = """
        You are an expert in creating mathematical and physics visualizations using Manim (Mathematical Animation Engine).
        Your task is to convert a text prompt into valid, executable Manim Python code.
        
        IMPORTANT RULES FOR COMPILATION SUCCESS:
        1. Only return valid Python code that works with the latest version of Manim Community edition
        2. Do NOT include any explanations outside of code comments
        3. Use ONLY the Scene class as the base class
        4. Include ALL necessary imports at the top (from manim import *)
        5. Use descriptive variable names that follow Python conventions
        6. Include helpful comments for complex parts of the visualization
        7. The class name MUST be "Screen" - always use this exact name
        8. Always implement the construct method correctly
        9. Ensure all objects are properly added to the scene with self.play() or self.add()
        10. Do not create custom classes other than the main Scene class
        11. Include proper self.wait() calls after animations for better viewing
        12. Check all mathematical expressions are valid LaTeX syntax
        13. Avoid advanced or experimental Manim features that might not be widely available
        14. Keep animations under 20 seconds total for better performance
        15. Ensure all coordinates and dimensions are appropriate for the default canvas size
        16. DO NOT include any backticks (```) or markdown formatting in your response
        
        RESPOND WITH ONLY THE EXECUTABLE PYTHON CODE, NO INTRODUCTION OR EXPLANATION, NO MARKDOWN FORMATTING.
        """
        
        final_prompt = f"Create a Manim visualization that explains: {prompt}"
        
        logger.info(f"Generating code with model: {model_name}")
        
        response = client.chat.completions.create(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": final_prompt}
            ]
        )
        
        generated_code = response.choices[0].message.content
        
        # Strip markdown formatting if it appears in the response
        if "```python" in generated_code:
            generated_code = generated_code.split("```python")[1]
            if "```" in generated_code:
                generated_code = generated_code.split("```")[0]
        elif "```" in generated_code:
            generated_code = generated_code.split("```")[1]
            if "```" in generated_code:
                generated_code = generated_code.split("```")[0]
        
        # Remove any additional backticks that might cause syntax errors
        generated_code = generated_code.replace('```', '')
        
        # Ensure code starts with proper import
        if not generated_code.strip().startswith('from manim import'):
            generated_code = 'from manim import *\n\n' + generated_code
            
        return generated_code.strip()
        
    except Exception as e:
        logger.error(f"Error generating code: {e}")
        return f"Error generating code: {str(e)}"

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

def placeholder_for_examples(prompt, model, quality):
    code = """
from manim import *

class PythagoreanTheorem(Scene):
    def construct(self):
        # This is placeholder code for examples
        # Creating a right triangle
        triangle = Polygon(
            ORIGIN, 
            RIGHT * 3, 
            UP * 4, 
            color=WHITE
        )
        
        # Adding labels
        a = Text("a", font_size=30).next_to(triangle, DOWN)
        b = Text("b", font_size=30).next_to(triangle, RIGHT)
        c = Text("c", font_size=30).next_to(
            triangle.get_center(), 
            UP + LEFT
        )
        
        # Add to scene
        self.play(Create(triangle))
        self.play(Write(a), Write(b), Write(c))
        
        # Wait at the end
        self.wait(2)
"""
    return code, None, "Example mode: Click 'Generate Video' to actually process this example"

def process_prompt(prompt, model_name, quality="medium_quality"):
    try:
        code = generate_manim_code(prompt, model_name)
        video_path = render_manim_video(code, quality)
        return code, video_path
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        return f"Error: {str(e)}", None

def process_prompt_with_status(prompt, model, quality, progress=gr.Progress()):
    try:
        progress(0, desc="Starting...")
        
        progress(0.3, desc="Generating Manim code using AI...")
        code = generate_manim_code(prompt, model)
        
        progress(0.6, desc="Rendering video with Manim (this may take a few minutes)...")
        video_path = render_manim_video(code, quality)
        
        progress(1.0, desc="Complete")
        
        if not video_path or video_path.startswith("Error"):
            status = video_path if video_path else "Error: Failed to generate video."
            return code, None, status
        else:
            status = "Video generated successfully!"
            return code, video_path, status
            
    except Exception as e:
        logger.error(f"Error in processing: {e}")
        return (code if 'code' in locals() else "Error generating code"), None, f"Error: {str(e)}"

def create_interface():
    with gr.Blocks(title="Math & Physics Video Generator") as app:
        gr.Markdown("# Interactive Math & Physics Video Generator")
        gr.Markdown("Generate educational videos from text prompts using AI and Manim")
        
        with gr.Row():
            with gr.Column():
                model_dropdown = gr.Dropdown(
                    choices=AVAILABLE_MODELS,
                    value=AVAILABLE_MODELS[1],
                    label="Select AI Model"
                )
                quality_radio = gr.Radio(
                    choices=["low_quality", "medium_quality", "high_quality"],
                    value="medium_quality",
                    label="Output Quality (affects rendering time)"
                )
                prompt_input = gr.Textbox(
                    placeholder="Enter a mathematical or physics concept to visualize...",
                    label="Prompt",
                    lines=3
                )
                submit_btn = gr.Button("Generate Video", variant="primary")
                
                with gr.Accordion("Generated Manim Code", open=False):
                    code_output = gr.Code(
                        language="python",
                        label="Generated Manim Code",
                        lines=20
                    )
            
            with gr.Column():
                video_output = gr.Video(
                    label="Generated Animation",
                    width="100%",
                    height=500
                )
                status_output = gr.Textbox(
                    label="Status",
                    value="Ready. Enter a prompt and click 'Generate Video'.",
                    interactive=False
                )
        
        submit_btn.click(
            fn=process_prompt_with_status,
            inputs=[prompt_input, model_dropdown, quality_radio],
            outputs=[code_output, video_output, status_output]
        )
        
        gr.Examples(
            examples=[
                ["Explain the Pythagorean theorem", AVAILABLE_MODELS[1], "medium_quality"],
                ["Show how a pendulum works with damping", AVAILABLE_MODELS[1], "medium_quality"],
                ["Demonstrate the concept of derivatives in calculus", AVAILABLE_MODELS[1], "medium_quality"],
                ["Visualize the wave function of a particle in a box", AVAILABLE_MODELS[1], "medium_quality"],
                ["Explain how a capacitor charges and discharges", AVAILABLE_MODELS[1], "medium_quality"]
            ],
            inputs=[prompt_input, model_dropdown, quality_radio],
            fn=placeholder_for_examples
        )
    
    return app

if __name__ == "__main__":
    app = create_interface()
    app.launch(share=True)