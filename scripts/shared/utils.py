"""
Utility functions for the catechism conversion.
"""
import re
from typing import Dict, OrderedDict, Any, List
from collections import OrderedDict

from .models import Question, Section


def create_bible_url(verses: str) -> str:
    """Create a URL for BibleGateway search.
    
    Args:
        verses: Bible reference in the format "Book chapter:verse"
    
    Returns:
        URL to the BibleGateway search for the given verses
    """
    encoded_verses = verses.replace(' ', '+').replace(':', '%3A').replace(';', '%3B').replace(',', '%2C')
    return f"https://www.biblegateway.com/passage/?search={encoded_verses}&version=ESV"


def sort_questions(questions: Dict[str, Question]) -> OrderedDict[str, Question]:
    """Sort questions by their ID.
    
    Args:
        questions: Dictionary of questions with IDs as keys
        
    Returns:
        OrderedDict of questions sorted by ID
    """
    def sort_key(id_question_pair):
        q_id = id_question_pair[0]
        # Try to convert to float for numerical sorting, otherwise use string sorting
        return float(q_id) if q_id.replace('.', '', 1).isdigit() else q_id
        
    return OrderedDict(sorted(questions.items(), key=sort_key))


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters.
    
    Args:
        text: Text to escape
        
    Returns:
        Text with LaTeX special characters escaped
    """
    # Define LaTeX special characters and their escaped versions
    latex_special_chars = {
        '&': '\\&',
        '%': '\\%',
        '$': '\\$',
        '#': '\\#',
        '_': '\\_',
        '{': '\\{',
        '}': '\\}',
        '~': '\\textasciitilde{}',
        '^': '\\textasciicircum{}',
        '\\': '\\textbackslash{}',
    }
    
    # Replace all special characters with their escaped versions
    for char, replacement in latex_special_chars.items():
        text = text.replace(char, replacement)
    
    return text


def is_enumerated_list_item(text: str) -> bool:
    """Check if text starts with a number followed by a period.
    
    Args:
        text: Text to check
        
    Returns:
        True if the text starts with a number followed by a period, False otherwise
    """
    pattern = re.compile(r'^(\d+)\.\s')
    return bool(pattern.match(text))


def is_bracketed_list_item(text: str) -> bool:
    """Check if text starts with a bracketed number.
    
    Args:
        text: Text to check
        
    Returns:
        True if the text starts with a bracketed number, False otherwise
    """
    pattern = re.compile(r'^\[(\d+)\]\s')
    return bool(pattern.match(text))


def extract_list_item_number(text: str) -> str:
    """Extract the number from a list item.
    
    Args:
        text: List item text
        
    Returns:
        The number as a string
    """
    # Check for regular numbered list
    pattern = re.compile(r'^(\d+)\.\s')
    match = pattern.match(text)
    if match:
        return match.group(1)
    
    # Check for bracketed number
    pattern = re.compile(r'^\[(\d+)\]\s')
    match = pattern.match(text)
    if match:
        return match.group(1)
    
    # Default if no match
    return ""


def strip_list_item_number(text: str) -> str:
    """Remove the number prefix from a list item.
    
    Args:
        text: List item text
        
    Returns:
        Text without the number prefix
    """
    # Remove regular numbered list prefix
    text = re.sub(r'^(\d+)\.\s', '', text)
    # Remove bracketed number prefix
    text = re.sub(r'^\[(\d+)\]\s', '', text)
    return text


def detect_list_sections(sections: List[Section]) -> bool:
    """Determine if sections should be formatted as a list.
    
    Args:
        sections: List of Section objects
        
    Returns:
        True if sections should be formatted as a list, False otherwise
    """
    # Only examine non-empty sections
    non_empty_sections = [s for s in sections if s.text]
    if not non_empty_sections:
        return False
    
    # Check for numbered list items or bracketed numbers
    enum_count = sum(1 for s in non_empty_sections if 
                    is_enumerated_list_item(s.text) or is_bracketed_list_item(s.text))
    
    # If a significant number of sections are list items, format as a list
    return enum_count >= 3