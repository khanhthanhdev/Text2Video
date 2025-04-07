"""
Conversation memory management for the Manimation system.
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Store and manage conversation history and current state.
    """
    def __init__(self):
        self.history = []
        self.current_scenario = None
        self.current_code = None
    
    def add_interaction(self, prompt, scenario, code, video_path):
        """Add a new interaction to the conversation history."""
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
        """Get context information for refinement prompts."""
        if not self.history:
            return ""
        
        # Construct context from the last interaction
        last = self.history[-1]
        context = f"Previous prompt: {last['prompt']}\n"
        if self.current_scenario and hasattr(self.current_scenario, 'title'):
            context += f"Current animation title: {self.current_scenario.title}\n"
        return context
    
    def get_last_prompt(self):
        """Get the most recent prompt, or a default if none exists."""
        if not self.history:
            return "Mathematical animation"
        return self.history[-1]["prompt"]
