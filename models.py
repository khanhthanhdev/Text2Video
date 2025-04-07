"""
Pydantic models for the Text2Video application.
"""

from typing import List, Optional, Tuple
from pydantic import BaseModel, Field

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
