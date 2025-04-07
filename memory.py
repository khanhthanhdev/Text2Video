"""
Memory management for the Manimation application.
"""
from typing import List, Dict, Any, Optional
from models import AnimationScenario

class ConversationMemory:
    """
    Stores conversation history and current animation context.
    """
    def __init__(self):
        self.history = []
        self.current_scenario = None
        self.current_code = None
        self.last_video_path = None
    
    def add_prompt(self, prompt: str, complexity: str):
        """
        Add a user prompt to the history.
        
        Args:
            prompt (str): User prompt text
            complexity (str): Complexity level
        """
        # Create a scenario from the prompt
        self.current_scenario = AnimationScenario(
            title=f"Animation: {prompt[:30]}...",
            description=prompt,
            complexity=complexity
        )
        
        # Add to history
        self.history.append({
            "type": "prompt",
            "prompt": prompt,
            "complexity": complexity,
            "scenario": self.current_scenario
        })
    
    def add_result(self, code: str, video_path: Optional[str]):
        """
        Add a generation result to the history.
        
        Args:
            code (str): Generated Manim code
            video_path (str): Path to the rendered video file
        """
        self.current_code = code
        self.last_video_path = video_path
        
        # Add to history
        self.history.append({
            "type": "result",
            "code": code,
            "video_path": video_path
        })
    
    def add_feedback(self, feedback: str):
        """
        Add user feedback to the history.
        
        Args:
            feedback (str): User feedback text
        """
        # Add to history
        self.history.append({
            "type": "feedback",
            "feedback": feedback
        })
    
    def get_current_prompt(self) -> str:
        """Get the most recent prompt text."""
        for item in reversed(self.history):
            if item["type"] == "prompt":
                return item["prompt"]
        return ""
    
    def get_current_complexity(self) -> str:
        """Get the most recent complexity level."""
        for item in reversed(self.history):
            if item["type"] == "prompt":
                return item["complexity"]
        return "medium"

# Create a singleton instance of the memory object
memory = ConversationMemory()

# Export the class and instance
__all__ = ["ConversationMemory", "memory"]
