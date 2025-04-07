"""
AI Agents for the Manimation system.
"""

import os
from datetime import datetime
import logging
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai import Agent, RunContext

from models import AnimationPrompt
from config import DEFAULT_MODEL

# Configure logging
logger = logging.getLogger(__name__)

def create_agents():
    """Create and configure the AI agents."""
    # Create OpenAI model with Together API provider
    model = OpenAIModel(
        DEFAULT_MODEL,
        provider=OpenAIProvider(
            base_url='https://api.together.xyz/v1', 
            api_key=os.environ.get('TOGETHER_API_KEY')
        ),
    )
    
    # Create the manim code generation agent
    manim_agent = Agent(
        model,
        deps_type=AnimationPrompt,
        system_prompt=(
            "You are a specialized AI agent for creating mathematical animations. "
            "Your goal is to convert user descriptions into precise Manim code "
            "that visualizes mathematical and physics concepts clearly and elegantly."
        ),
    )
    
    # Create the layout optimization agent
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
    
    # Create the evaluation agent
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
    
    # Add tool functions to agents
    from tools import extract_scenario_direct, generate_code_direct
    
    @manim_agent.tool
    def extract_scenario(ctx: RunContext[AnimationPrompt]) -> AnimationScenario:
        """Extract a structured animation scenario from a text prompt."""
        prompt = ctx.deps
        # Use the extract_scenario_direct tool from tools.py
        return extract_scenario_direct(prompt.description, prompt.complexity)
    
    @manim_agent.tool
    def generate_code(ctx: RunContext[AnimationPrompt], scenario: AnimationScenario) -> str:
        """Generate Manim code from a structured scenario."""
        prompt = ctx.deps
        # Use the generate_code_direct tool from tools.py
        return generate_code_direct(prompt.description, scenario, prompt.complexity)
    
    return {
        "manim_agent": manim_agent,
        "layout_agent": layout_agent, 
        "evaluation_agent": evaluation_agent
    }
