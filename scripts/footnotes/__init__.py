"""
Functions for processing catechism footnotes (Bible references).
"""
from typing import List
import math

from shared.models import Footnote
from shared.utils import create_bible_url, escape_latex


def process_footnotes(footnotes: List[Footnote]) -> str:
    """Process footnotes into a LaTeX format."""
    if not footnotes:
        return ""
    
    # Add URLs to footnotes if not already present
    for footnote in footnotes:
        if not footnote.url:
            footnote.url = create_bible_url(footnote.verses)
    
    # Create a framed box with columns for the references
    latex = "\\begin{mdframed}[linecolor=blue!20,backgroundcolor=blue!5,linewidth=1pt,skipabove=20pt,skipbelow=20pt,innertopmargin=0pt,innerbottommargin=15pt]\n"
    latex += "\\setlength{\\columnsep}{2em}\n"
    latex += "\\setlength{\\parindent}{0pt}\n"
    latex += "\\begin{multicols}{2}\n"
    latex += "\\footnotesize\\color[RGB]{0, 0, 150}\n"
    
    # Process each footnote with proper line breaks
    for footnote in footnotes:
        escaped_verses = escape_latex(footnote.verses)
        latex += f"$^{{{footnote.number}}}$ \\href{{{footnote.url}}}{{{escaped_verses}}}\\\\\n"
    
    # Close the environments
    latex += "\\end{multicols}\n"
    latex += "\\end{mdframed}"
    
    return latex