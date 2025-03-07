"""
Functions for processing catechism questions.
"""
from shared.models import Question
from shared.utils import escape_latex


def process_question(question: Question) -> str:
    """Process a question into LaTeX format with explicit hyperref targets."""
    # Escape special LaTeX characters in the question text
    escaped_question = escape_latex(question.question)
    
    # Create a unique label for the question
    question_label = f"q{question.id.replace('.', '-')}"
    
    # Format as a section with custom styling and explicit hyperref target
    latex = f"\\hypertarget{{{question_label}}}{{\\section{{Q. {question.id}: {escaped_question}}}}}"
    
    return latex