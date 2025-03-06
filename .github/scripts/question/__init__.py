"""
Functions for processing catechism questions.
"""
from shared.models import Question
from shared.utils import escape_latex


def process_question(question: Question) -> str:
    """Process a question into LaTeX format.
    
    Args:
        question: Question object to process
        
    Returns:
        LaTeX representation of the question
    """
    # Escape special LaTeX characters in the question text
    escaped_question = escape_latex(question.question)
    
    # Format as a section with custom styling
    latex = f"\\section{{Q. {question.id}: {escaped_question}}}"
    
    return latex