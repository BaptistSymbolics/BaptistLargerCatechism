#!/usr/bin/env python3
"""
Convert catechism TOML files directly to LaTeX for better control and debugging.
"""
from __future__ import annotations
import toml
import glob
import argparse
from pathlib import Path
from typing import Dict, List, Optional

from question import process_question
from answer import process_answer
from footnotes import process_footnotes
from shared.models import Question, Section, Footnote
from shared.utils import create_bible_url, sort_questions


def load_toml_file(file_path: str) -> List[Question]:
    """Load and parse a TOML file into Question objects."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = toml.load(file)
            
        questions = []
        # Handle single question file
        if isinstance(data, dict) and 'id' in data and 'question' in data:
            questions.append(parse_question_data(data))
        # Handle multiple question file
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and 'id' in item and 'question' in item:
                    questions.append(parse_question_data(item))
        
        return questions
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return []


def parse_question_data(data: Dict) -> Question:
    """Parse raw question data into a Question object."""
    sections = []
    for section_data in data.get('sections', []):
        sections.append(Section(
            text=section_data.get('text', '').strip(),
            verses=section_data.get('verses', '').strip()
        ))
    
    return Question(
        id=data.get('id', ''),
        question=data.get('question', ''),
        sections=sections
    )


def find_toml_files(directory: str) -> List[str]:
    """Find all TOML files in the specified directory."""
    return glob.glob(f'{directory}/*.toml')


def process_files(file_paths: List[str]) -> Dict[str, Question]:
    """Process all TOML files and return sorted questions."""
    all_questions = {}
    
    for file_path in file_paths:
        questions = load_toml_file(file_path)
        for question in questions:
            all_questions[question.id] = question
    
    return sort_questions(all_questions)


def generate_latex_preamble() -> str:
    """Generate the LaTeX preamble with document class and package imports."""
    preamble = "\\documentclass[12pt,article]{article}\n"
    
    # Base packages
    preamble += "\\usepackage{geometry}\n"
    preamble += "\\geometry{margin=1in}\n"
    preamble += "\\usepackage{titlesec}\n"
    preamble += "\\usepackage{xcolor}\n"
    preamble += "\\usepackage{fancyhdr}\n"
    preamble += "\\usepackage{fontspec}\n"
    preamble += "\\setmainfont[Path=./fonts/,UprightFont=EBGaramond12-Regular.otf,ItalicFont=EBGaramond12-Italic.otf]{EB Garamond}\n"
    preamble += "\\usepackage{setspace}\n"
    preamble += "\\onehalfspacing\n"
    preamble += "\\usepackage{mdframed}\n"
    preamble += "\\usepackage{multicol}\n"
    preamble += "\\usepackage{enumitem}\n"
    preamble += "\\usepackage{bookmark}\n"  # For better PDF bookmarks
    
    # TOC formatting - load before hyperref
    preamble += "\\usepackage{tocloft}\n"
    preamble += "\\setlength{\\cftbeforesecskip}{10pt}\n"
    preamble += "\\renewcommand{\\cftsecfont}{\\bfseries}\n"
    
    # Hyperref should be loaded last to avoid conflicts
    preamble += "\\usepackage{hyperref}\n"
    preamble += "\\hypersetup{\n"
    preamble += "  colorlinks=true,\n"
    preamble += "  linkcolor=blue,\n"
    preamble += "  urlcolor=blue,\n"
    preamble += "  citecolor=blue,\n"
    preamble += "  linktoc=all,\n"
    preamble += "  bookmarksnumbered=true,\n"
    preamble += "  bookmarksopen=true\n"
    preamble += "}\n"
    
    # Remove section numbering
    preamble += "\\setcounter{secnumdepth}{0}\n"
    
    # Format section headings
    preamble += "\\titleformat{\\section}{\\LARGE\\bfseries\\color[RGB]{231, 76, 60}}{\\thesection}{1em}{}\n"
    preamble += "\\titleformat{\\subsection}{\\Large\\bfseries\\color{black}}{\\thesubsection}{1em}{}\n"
    
    # Setup page headers and footers
    preamble += "\\pagestyle{fancy}\n"
    preamble += "\\fancyhead[R]{The Baptist Larger Catechism}\n"
    preamble += "\\fancyhead[L]{\\thepage}\n"
    preamble += "\\fancyfoot{}\n"
    
    return preamble


def generate_latex_document_start() -> str:
    """Generate the LaTeX document start with title and TOC."""
    content = "\\begin{document}\n\n"
    content += "\\title{The Baptist Larger Catechism}\n"
    content += "\\maketitle\n"
    content += "\\tableofcontents\n"
    content += "\\newpage\n\n"
    return content


def generate_latex_document_end() -> str:
    """Generate the LaTeX document end."""
    return "\\end{document}\n"


def generate_latex(questions: Dict[str, Question], template_path: Optional[str] = None) -> str:
    """Generate complete LaTeX content from questions."""
    # Generate the document structure
    latex = generate_latex_preamble()
    latex += generate_latex_document_start()
    
    # Process each question
    for q_id, question in sorted(questions.items(), key=lambda x: float(x[0]) if x[0].replace('.', '', 1).isdigit() else x[0]):
        q_latex = process_question(question)
        a_latex, footnotes = process_answer(question)
        f_latex = process_footnotes(footnotes)
        
        section_latex = f"{q_latex}\n\n{a_latex}\n\n{f_latex}\n\n\\hrulefill\n\n"
        latex += section_latex
    
    latex += generate_latex_document_end()
    return latex


def save_latex(content: str, output_path: str) -> None:
    """Save LaTeX content to a file."""
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Conversion complete. LaTeX file created: {output_path}")


def main() -> None:
    """Main function to orchestrate the conversion process."""
    parser = argparse.ArgumentParser(description='Convert TOML catechism files to LaTeX')
    parser.add_argument('-s', '--source', default='src', help='Source directory containing TOML files')
    parser.add_argument('-o', '--output', default='larger-catechism.tex', help='Output LaTeX file')
    parser.add_argument('-t', '--template', help='Optional LaTeX template file')
    
    args = parser.parse_args()
    
    # Find TOML files
    toml_files = find_toml_files(args.source)
    if not toml_files:
        print(f"No TOML files found in the {args.source} directory.")
        return
    
    # Process files
    questions = process_files(toml_files)
    
    # Generate LaTeX
    latex_content = generate_latex(questions, args.template)
    
    # Save the result
    save_latex(latex_content, args.output)


if __name__ == "__main__":
    main()