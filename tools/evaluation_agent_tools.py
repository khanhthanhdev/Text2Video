from agents import evaluation_agent
from models import AnimationPrompt, EvaluationResult
from config import DEFAULT_MODEL, logger, client, llm
import re
import json
from typing import Optional, Dict, Any, List
from pydantic_ai import RunContext

@evaluation_agent.tool
def check_syntax_errors(ctx: RunContext[AnimationPrompt], code: str) -> List[str]:
    """Check for Python and Manim-specific syntax errors."""
    prompt = ctx.deps
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Analyze this Manim code for syntax errors and logical mistakes. Look for:

1. Python syntax errors (missing colons, parentheses, indentation problems)
2. Manim-specific errors (incorrect class usage, invalid animation methods)
3. Undefined variables or objects that are used before definition
4. Incorrect parameter types or values
5. Missing imports or misused Manim classes
6. LaTeX syntax errors in MathTex objects
7. Animation errors (using wrong objects in animations, incorrect method calls)

For each error found, provide:
1. The line number or code region with the error
2. A description of what's wrong
3. A suggested fix

Be thorough but only focus on actual errors, not style issues.
"""
            },
            {"role": "user", "content": f"Check this Manim code for syntax errors:\n\n```python\n{code}\n```\n\nPrompt: {prompt.description}, Complexity: {prompt.complexity}"}
        ]
    )
    
    # Extract errors from response
    error_content = response.choices[0].message.content
    error_lines = error_content.split('\n')
    
    # Filter for actual errors
    errors = []
    current_error = ""
    for line in error_lines:
        if line.strip().startswith(("Error", "Issue", "Problem", "Bug", "Line", "1.", "2.", "3.", "4.", "5.")):
            if current_error:
                errors.append(current_error.strip())
            current_error = line.strip()
        elif current_error and line.strip():
            current_error += " " + line.strip()
    
    # Add the last error if there is one
    if current_error:
        errors.append(current_error.strip())
    
    return errors

@evaluation_agent.tool
def check_positioning(ctx: RunContext[AnimationPrompt], code: str) -> dict:
    """Check for proper positioning and potential overlaps in the animation."""
    prompt = ctx.deps
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Analyze this Manim code specifically for positioning and spacing issues. Look for:

1. Objects without explicit position commands (move_to, shift, to_edge, etc.)
2. Elements that might overlap based on their coordinates
3. Text or equations positioned too close to each other
4. Elements positioned too close to the edge of the screen
5. Improper grouping of related elements
6. Elements with undefined positioning that might appear at origin (0,0)
7. Animations where multiple elements move to the same location

Analyze the coordinates and create a mental map of where objects are positioned.
Flag any positions where elements might overlap or be too close (less than 1.0 units apart).

Respond with a JSON object containing:
- positioning_issues: List of positioning problems found
- overlap_issues: List of specific coordinates or elements that might overlap
- suggestions: Specific suggestions to improve positioning
"""
            },
            {"role": "user", "content": f"Analyze this Manim code for positioning and spacing issues:\n\n```python\n{code}\n```\n\nPrompt: {prompt.description}, Complexity: {prompt.complexity}"}
        ]
    )
    
    content = response.choices[0].message.content
    
    try:
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            positioning_analysis = json.loads(json_str)
            return positioning_analysis
    except Exception as e:
        logger.error(f"Error parsing positioning analysis: {e}")
    
    # If no valid JSON is found, extract information manually
    positioning_issues = []
    overlap_issues = []
    suggestions = []
    
    # Simple pattern matching to extract issues
    for line in content.split('\n'):
        line = line.strip()
        if "position" in line.lower() or "coordinate" in line.lower() or "overlap" in line.lower():
            if line.startswith(("- ", "* ", "1. ", "2. ")):
                positioning_issues.append(line.lstrip("- *123456789. "))
        if "overlap" in line.lower():
            if line.startswith(("- ", "* ", "1. ", "2. ")):
                overlap_issues.append(line.lstrip("- *123456789. "))
        if "suggest" in line.lower() or "should" in line.lower() or "could" in line.lower():
            if line.startswith(("- ", "* ", "1. ", "2. ")):
                suggestions.append(line.lstrip("- *123456789. "))
    
    return {
        "positioning_issues": positioning_issues,
        "overlap_issues": overlap_issues,
        "suggestions": suggestions
    }

@evaluation_agent.tool
def fix_code_issues(ctx: RunContext[AnimationPrompt], code: str, syntax_errors: List[str], positioning_issues: dict) -> str:
    """Fix detected issues in the code."""
    prompt = ctx.deps
    
    # Format issues for the prompt
    syntax_errors_str = "\n".join([f"- {error}" for error in syntax_errors])
    
    positioning_issues_str = ""
    if "positioning_issues" in positioning_issues:
        positioning_issues_str += "\nPositioning Issues:\n" + "\n".join([f"- {issue}" for issue in positioning_issues["positioning_issues"]])
    
    if "overlap_issues" in positioning_issues:
        positioning_issues_str += "\nOverlap Issues:\n" + "\n".join([f"- {issue}" for issue in positioning_issues["overlap_issues"]])
    
    if "suggestions" in positioning_issues:
        positioning_issues_str += "\nSuggestions:\n" + "\n".join([f"- {suggestion}" for suggestion in positioning_issues["suggestions"]])
    
    response = client.chat.completions.create(
        model=llm,
        messages=[
            {"role": "system", "content": """
Fix the provided Manim code by addressing all identified issues. Follow these guidelines:

1. Fix all syntax errors and logical mistakes first
2. Fix positioning issues by adding explicit positioning commands
3. Resolve element overlaps by repositioning elements with adequate spacing
4. Implement all positioning suggestions to improve clarity
5. Maintain the original educational intent and mathematical content
6. Ensure all animations follow a logical step-by-step flow
7. Add comments explaining your fixes for complex changes

Return the complete, corrected code ready for rendering.
"""
            },
            {"role": "user", "content": 
                f"Fix the following Manim code by addressing these issues:\n\n"
                f"Syntax Errors:\n{syntax_errors_str}\n\n"
                f"Positioning Issues:{positioning_issues_str}\n\n"
                f"Original Code:\n```python\n{code}\n```\n\n"
                f"Original Prompt: {prompt.description}, Complexity: {prompt.complexity}\n\n"
                f"Return the complete fixed code."
            }
        ]
    )
    
    fixed_code = response.choices[0].message.content
    
    # Clean up the response to extract just the code
    if "```python" in fixed_code:
        fixed_code = fixed_code.split("```python", 1)[1]
    if "```" in fixed_code:
        fixed_code = fixed_code.split("```", 1)[0]
    
    return fixed_code.strip()

@evaluation_agent.tool
def evaluate_code(ctx: RunContext[AnimationPrompt], code: str) -> EvaluationResult:
    """Evaluate Manim code for errors and positioning issues."""
    # Check for syntax errors
    syntax_errors = check_syntax_errors(ctx, code)
    
    # Check for positioning issues
    positioning_analysis = check_positioning(ctx, code)
    
    positioning_issues = positioning_analysis.get("positioning_issues", [])
    overlap_issues = positioning_analysis.get("overlap_issues", [])
    suggestions = positioning_analysis.get("suggestions", [])
    
    # Determine if there are errors
    has_errors = len(syntax_errors) > 0 or len(positioning_issues) > 0 or len(overlap_issues) > 0
    
    # If there are errors, fix the code
    fixed_code = None
    if has_errors:
        fixed_code = fix_code_issues(ctx, code, syntax_errors, positioning_analysis)
    
    return EvaluationResult(
        has_errors=has_errors,
        syntax_errors=syntax_errors,
        positioning_issues=positioning_issues,
        overlap_issues=overlap_issues,
        suggestions=suggestions,
        fixed_code=fixed_code
    )