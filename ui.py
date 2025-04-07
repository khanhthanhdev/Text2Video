from animation import generate_animation

def gradio_interface(prompt: str, complexity: str = "medium", quality: str = "medium_quality"):
    code, video_path, log_output = generate_animation(prompt, complexity, quality)
    if video_path and not video_path.startswith("Error"):
        return code, video_path, log_output
    else:
        return code, None, log_output