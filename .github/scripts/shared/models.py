"""
Data models for the catechism conversion.
"""
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Section:
    """Represents a section of a catechism question with text and verses."""
    text: str
    verses: str


@dataclass
class Question:
    """Represents a catechism question with its sections."""
    id: str
    question: str
    sections: List[Section]


@dataclass
class Footnote:
    """Represents a footnote with number and verse references."""
    number: int
    verses: str
    url: Optional[str] = None