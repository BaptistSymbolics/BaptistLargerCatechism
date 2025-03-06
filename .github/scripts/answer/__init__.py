"""
Functions for processing catechism answers.
"""
from typing import List, Tuple, Dict
import re

from shared.models import Question, Section, Footnote
from shared.utils import (
    escape_latex, 
    detect_list_sections,
    is_enumerated_list_item,
    is_bracketed_list_item,
    extract_list_item_number,
    strip_list_item_number
)


def process_answer(question: Question) -> Tuple[str, List[Footnote]]:
    """Process a question's answer into LaTeX format.
    
    Args:
        question: Question object to process
        
    Returns:
        Tuple of (LaTeX representation of the answer, List of footnotes)
    """
    # Check if the answer contains list items
    if detect_list_sections(question.sections):
        return process_list_answer(question.sections)
    else:
        return process_regular_answer(question.sections)


def process_regular_answer(sections: List[Section]) -> Tuple[str, List[Footnote]]:
    """Process a regular (non-list) answer into LaTeX format.
    
    Args:
        sections: List of Section objects
        
    Returns:
        Tuple of (LaTeX representation of the answer, List of footnotes)
    """
    # Build the answer text with footnote markers
    latex = "A: "
    footnotes = []
    footnote_counter = 1
    
    for section in sections:
        if not section.text:
            continue
        
        # Escape special LaTeX characters
        escaped_text = escape_latex(section.text)
        
        if section.verses:
            # Add a superscript footnote reference
            latex += f"{escaped_text}$^{{{footnote_counter}}}$ "
            footnotes.append(Footnote(
                number=footnote_counter,
                verses=section.verses
            ))
            footnote_counter += 1
        else:
            latex += f"{escaped_text} "
    
    return latex.strip(), footnotes


def process_list_answer(sections: List[Section]) -> Tuple[str, List[Footnote]]:
    """Process an answer with list items into LaTeX format.
    
    Args:
        sections: List of Section objects
        
    Returns:
        Tuple of (LaTeX representation of the answer, List of footnotes)
    """
    # Separate regular text from list items
    list_sections = []
    regular_sections = []
    
    for section in sections:
        if not section.text:
            continue
        
        if is_enumerated_list_item(section.text) or is_bracketed_list_item(section.text):
            list_sections.append(section)
        else:
            regular_sections.append(section)
    
    # Process regular text
    intro_latex, footnotes = process_regular_answer(regular_sections)
    
    # Start footnote counter after the intro footnotes
    footnote_counter = len(footnotes) + 1
    
    # Format list items
    if list_sections:
        # Add a blank line after the intro
        if intro_latex:
            intro_latex += "\n\n"
        
        # Start a LaTeX enumerate environment
        list_latex = "\\begin{enumerate}\n"
        
        for section in list_sections:
            # Escape special LaTeX characters
            escaped_text = escape_latex(strip_list_item_number(section.text))
            
            if section.verses:
                # Add a list item with a footnote reference
                list_latex += f"\\item {escaped_text}$^{{{footnote_counter}}}$\n"
                footnotes.append(Footnote(
                    number=footnote_counter,
                    verses=section.verses
                ))
                footnote_counter += 1
            else:
                # Add a plain list item
                list_latex += f"\\item {escaped_text}\n"
        
        # End the enumerate environment
        list_latex += "\\end{enumerate}"
        
        # Combine intro and list
        full_latex = intro_latex + list_latex
    else:
        full_latex = intro_latex
    
    return full_latex, footnotes