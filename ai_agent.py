"""
AI Agent for generating Manim animations from text prompts using pydantic-ai.
"""
import os
from dotenv import load_dotenv
import gradio as gr
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
import openai

# Make sure to import all needed models explicitly
from models import AnimationPrompt, AnimationScenario, AnimationResult, LayoutConfiguration, EvaluationResult

from config import get_openai_client, get_output_directories, render_manim_video

# Comment out imports that are causing issues until we can determine correct paths
# from tools.manim_agent_tools import render_manim_video, format_log_output, refine_animation, optimize_element_positioning, extract_scenario_direct, generate_code_direct
# from tools.layout_agent_tools import analyze_element_layout, optimize_layout
# from tools.evaluation_agent_tools import check_syntax_errors, check_positioning, fix_code_issues, evaluate_code

# Keep imports that are working
from renderer import render_manim_video  # Use this instead of the one from tools
from utils.log import logger, format_log_output
from memory import memory
from animation import generate_animation, refine_animation, rerender_animation, evaluate_and_fix_manim_code
from utils.code_gen import generate_code_direct
from utils.layout import direct_optimize_layout, direct_analyze_layout, optimize_element_positioning, direct_evaluate_and_fix

load_dotenv()

# Configure OpenAI client to use Together API
client = openai.OpenAI(
    api_key=os.environ.get("TOGETHER_API_KEY"),
    base_url="https://api.together.xyz/v1",
)

llm = "deepseek-ai/DeepSeek-V3"

model = OpenAIModel(
    'deepseek-ai/DeepSeek-V3',
    provider=OpenAIProvider(
        base_url='https://api.together.xyz/v1', api_key=os.environ.get('TOGETHER_API_KEY')
    ),
)

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
            
            # Fix the video path handling - ensure it's a valid path before using it
            if video_path and isinstance(video_path, str) and os.path.exists(video_path):
                # Use a relative path or full URL depending on the environment
                if is_huggingface:
                    # On HuggingFace, use a path relative to the app
                    relative_path = os.path.relpath(video_path, "/tmp")
                    video_display = f"![Animation]({relative_path})"
                else:
                    # For local development, use a direct file path
                    video_display = f"Video saved at: {video_path}"
                
                bot_message = f"{bot_message}\n\n{video_display}"
            
            history.append((None, bot_message))  # Bot message
            return history
        
        # Function wrappers for UI updates with chat history
        def generate_and_update_chat(prompt, complexity, quality, history):
            code, video_path, log = generate_animation(prompt, complexity, quality)
            
            # Get the scenario title from memory if available
            scenario_title = "Animation"
            if hasattr(memory, 'current_scenario') and memory.current_scenario:
                scenario_title = memory.current_scenario.title
            
            new_history = update_chat_history(
                history, 
                f"**Create animation:** {prompt}",
                f"**Generated animation:** {scenario_title}", 
                video_path
            )
            
            # Return video_path directly without trying to access .objects
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


