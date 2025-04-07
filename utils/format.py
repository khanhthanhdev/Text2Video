from models import EvaluationResult

def format_evaluation_results(result: EvaluationResult) -> str:
    """Format evaluation results for display."""
    output = "## Code Evaluation Results\n\n"
    
    if not result.has_errors:
        output += "✅ No errors or positioning issues detected. Code looks good!\n\n"
        return output
    
    if result.syntax_errors:
        output += "### Syntax Errors\n\n"
        for i, error in enumerate(result.syntax_errors):
            output += f"{i+1}. {error}\n"
        output += "\n"
    
    if result.positioning_issues:
        output += "### Positioning Issues\n\n"
        for i, issue in enumerate(result.positioning_issues):
            output += f"{i+1}. {issue}\n"
        output += "\n"
    
    if result.overlap_issues:
        output += "### Potential Element Overlaps\n\n"
        for i, issue in enumerate(result.overlap_issues):
            output += f"{i+1}. {issue}\n"
        output += "\n"
    
    if result.suggestions:
        output += "### Suggestions for Improvement\n\n"
        for i, suggestion in enumerate(result.suggestions):
            output += f"{i+1}. {suggestion}\n"
        output += "\n"
    
    if result.fixed_code:
        output += "✅ These issues have been automatically fixed in the updated code.\n"
    else:
        output += "❌ Could not automatically fix all issues. Please review the code manually.\n"
    
    return output