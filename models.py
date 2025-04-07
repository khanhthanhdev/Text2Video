"""
Data models for the Manimation application.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class AnimationPrompt(BaseModel):
    """User input for animation generation"""
    description: str = Field(..., description="Textual description of the desired animation")
    complexity: str = Field("medium", description="Complexity level: simple, medium, complex")
    duration: Optional[float] = Field(None, description="Desired duration in seconds")
    style_preferences: Optional[Dict[str, Any]] = Field(None, description="Style preferences")

class AnimationScenario(BaseModel):
    """Structured representation of an animation concept"""
    title: str = Field(..., description="Title of the animation")
    description: str = Field(..., description="Detailed description")
    complexity: str = Field("medium", description="Complexity level")
    elements: Optional[List[Dict[str, Any]]] = Field(None, description="Mathematical elements to include")
    animations: Optional[List[Dict[str, Any]]] = Field(None, description="Animation sequence details")

class LayoutConfiguration(BaseModel):
    """Configuration for layout of elements"""
    canvas_size: tuple = Field((8, 4.5), description="Canvas dimensions (width, height)")
    margin: float = Field(0.5, description="Margin around elements")
    spacing: float = Field(0.3, description="Spacing between elements")
    positioning: Optional[Dict[str, Any]] = Field(None, description="Specific positioning instructions")

class AnimationResult(BaseModel):
    """Result of animation generation"""
    code: str = Field(..., description="Generated Manim code")
    video_path: Optional[str] = Field(None, description="Path to rendered video")
    log: Optional[str] = Field(None, description="Processing log")
    error: Optional[str] = Field(None, description="Error message if any")

class EvaluationResult(BaseModel):
    """Result of code evaluation"""
    original_code: str = Field(..., description="Original code evaluated")
    fixed_code: str = Field(..., description="Fixed code after evaluation")
    issues: List[Dict[str, Any]] = Field(default_factory=list, description="Issues found")
    report: str = Field(..., description="Evaluation report")
