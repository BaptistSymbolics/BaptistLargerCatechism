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


def detect_hierarchical_answer(sections: List[Section]) -> bool:
    """Detect if the answer has a hierarchical structure with numbered main sections."""
    # Look for sections that start with patterns like "1. From" or "2. From"
    hierarchical_pattern = re.compile(r'^\d+\.\s+From\s+')
    
    # Check if there are multiple (3+) sections matching this pattern
    hierarchical_sections = [s for s in sections if s.text and hierarchical_pattern.match(s.text)]
    return len(hierarchical_sections) >= 3


def process_answer(question: Question) -> Tuple[str, List[Footnote]]:
    """Process a question's answer into LaTeX format.
    
    Args:
        question: Question object to process
        
    Returns:
        Tuple of (LaTeX representation of the answer, List of footnotes)
    """
    # First check if this is a hierarchical answer
    if detect_hierarchical_answer(question.sections):
        return process_hierarchical_answer(question.sections)
    # Then check if it's a regular list
    elif detect_list_sections(question.sections):
        return process_list_answer(question.sections)
    # Otherwise process as regular text
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


def process_hierarchical_answer(sections: List[Section]) -> Tuple[str, List[Footnote]]:
    """Process an answer with hierarchical numbered sections."""
    latex = "A: "
    footnotes = []
    footnote_counter = 1
    
    # Track the current section number
    current_section = None
    section_started = False
    
    # First pass: determine where each numbered section begins
    section_indices = {}
    for i, section in enumerate(sections):
        if not section.text:
            continue
            
        match = re.match(r'^(\d+)\.\s+From\s+(.*)', section.text)
        if match:
            section_num = int(match.group(1))
            section_indices[section_num] = i
    
    # Find the first "Sins become more harmful:" text
    intro_text = None
    for i, section in enumerate(sections):
        if not section.text:
            continue
            
        if "Sins become more harmful:" in section.text:
            intro_text = section.text.split("Sins become more harmful:")[0] + "Sins become more harmful:"
            # Remove this part from the section text to avoid duplication
            sections[i].text = section.text.replace(intro_text, "").strip()
            break
    
    # Start with the intro
    if intro_text:
        latex += f"{intro_text}\n\n"
    
    # Process each section with proper formatting and spacing
    last_section_num = 0
    
    for i, section in enumerate(sections):
        if not section.text:
            continue
        
        # Check if this is a new section
        section_match = re.match(r'^(\d+)\.\s+From\s+(.*)', section.text)
        if section_match:
            section_num = int(section_match.group(1))
            section_text = section_match.group(2)
            
            # Add proper formatting and spacing
            latex += f"{section_num}. {section_text}"
            last_section_num = section_num
        else:
            # Regular text
            escaped_text = escape_latex(section.text)
            if escaped_text:
                latex += f"{escaped_text}"
        
        # Add footnote if present
        if section.verses:
            latex += f"$^{{{footnote_counter}}}$ "
            footnotes.append(Footnote(number=footnote_counter, verses=section.verses))
            footnote_counter += 1
        else:
            latex += " "
        
        # Check if next section is a new numbered section
        new_section_coming = False
        for j in range(i+1, len(sections)):
            if sections[j].text and re.match(r'^(\d+)\.\s+From\s+(.*)', sections[j].text):
                new_section_coming = True
                break
            elif sections[j].text:
                break
        
        if new_section_coming:
            latex += "\n\n"
    
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