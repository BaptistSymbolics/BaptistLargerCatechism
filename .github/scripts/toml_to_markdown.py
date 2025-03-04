#!/usr/bin/env python3
"""
Convert catechism TOML files to a formatted Markdown file using functional programming principles.
"""
import toml
import re
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional, OrderedDict, Any, Iterator, Callable
from collections import OrderedDict
from dataclasses import dataclass

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

def load_toml_file(file_path: str) -> List[Question]:
    """Load and parse a TOML file into Question objects."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            data = toml.load(file)
            
        questions = []
        # Handle single question file
        if 'id' in data and 'question' in data:
            questions.append(parse_question_data(data))
        # Handle multiple question file
        elif isinstance(data, list):
            for item in data:
                if 'id' in item and 'question' in item:
                    questions.append(parse_question_data(item))
        
        return questions
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return []

def parse_question_data(data: Dict[str, Any]) -> Question:
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

def is_enumerated_list_item(text: str) -> bool:
    """Check if text starts with a number followed by a period."""
    list_item_pattern = re.compile(r'^(\d+)\.\s')
    return bool(list_item_pattern.match(text))

def should_format_as_enumerated_list(sections: List[Section]) -> bool:
    """Determine if sections should be formatted as an enumerated list."""
    non_empty_sections = [s for s in sections if s.text]
    if not non_empty_sections:
        return False
    
    enum_count = sum(1 for s in non_empty_sections if is_enumerated_list_item(s.text))
    return enum_count >= 3

def get_list_item_number(text: str) -> Optional[str]:
    """Extract the number from a list item."""
    list_item_pattern = re.compile(r'^(\d+)\.\s')
    match = list_item_pattern.match(text)
    return match.group(1) if match else None

def strip_list_item_number(text: str) -> str:
    """Remove the number prefix from a list item."""
    list_item_pattern = re.compile(r'^(\d+)\.\s')
    return list_item_pattern.sub('', text)

def create_bible_url(verses: str) -> str:
    """Create a URL for BibleGateway search."""
    encoded_verses = verses.replace(' ', '+').replace(':', '%3A').replace(';', '%3B').replace(',', '%2C')
    return f"https://www.biblegateway.com/passage/?search={encoded_verses}&version=ESV"

def format_footnotes(footnotes: List[Footnote]) -> str:
    """Format a list of footnotes as markdown."""
    markdown = ""
    for footnote in footnotes:
        if footnote.verses:
            bible_url = create_bible_url(footnote.verses)
            markdown += f"{footnote.number}. [{footnote.verses}]({bible_url})\n"
    return markdown

def format_regular_sections(sections: List[Section]) -> Tuple[str, List[Footnote]]:
    """Format sections as continuous text with footnotes."""
    full_text = ""
    footnotes = []
    footnote_counter = 1
    
    for section in sections:
        if not section.text:
            continue
            
        if section.verses:
            full_text += f"{section.text}$^{{{footnote_counter}}}$ "
            footnotes.append(Footnote(footnote_counter, section.verses))
            footnote_counter += 1
        else:
            full_text += f"{section.text} "
    
    return full_text.strip(), footnotes

def format_enumerated_list(sections: List[Section]) -> Tuple[str, str, List[Footnote]]:
    """Format sections as an enumerated list with intro text and footnotes."""
    # First extract non-list text
    intro_text, intro_footnotes = format_non_list_items(sections)
    
    # Then format list items
    list_text = ""
    list_footnotes = []
    footnote_counter = len(intro_footnotes) + 1
    first_item = True
    
    for section in sections:
        if not section.text or not is_enumerated_list_item(section.text):
            continue
        
        num = get_list_item_number(section.text)
        text = strip_list_item_number(section.text)
        
        if not first_item:
            list_text += "\n"
        first_item = False
        
        if section.verses:
            list_text += f"{num}. {text}$^{{{footnote_counter}}}$"
            list_footnotes.append(Footnote(footnote_counter, section.verses))
            footnote_counter += 1
        else:
            list_text += f"{num}. {text}"
    
    return intro_text, list_text, intro_footnotes + list_footnotes

def format_non_list_items(sections: List[Section]) -> Tuple[str, List[Footnote]]:
    """Format only the non-list items from sections."""
    full_text = ""
    footnotes = []
    footnote_counter = 1
    
    for section in sections:
        if not section.text or is_enumerated_list_item(section.text):
            continue
            
        if section.verses:
            full_text += f"{section.text}$^{{{footnote_counter}}}$ "
            footnotes.append(Footnote(footnote_counter, section.verses))
            footnote_counter += 1
        else:
            full_text += f"{section.text} "
    
    return full_text.strip(), footnotes

def format_question(question: Question) -> str:
    """Format a question into markdown."""
    markdown = f"# Q. {question.id}: {question.question}\n\n"
    markdown += "A: "
    
    if should_format_as_enumerated_list(question.sections):
        intro_text, list_text, footnotes = format_enumerated_list(question.sections)
        
        if intro_text:
            markdown += intro_text + "\n\n"
        
        if list_text:
            markdown += list_text + "\n\n"
    else:
        full_text, footnotes = format_regular_sections(question.sections)
        markdown += full_text + "\n\n"
    
    # Add footnotes
    markdown += format_footnotes(footnotes)
    markdown += "\n---\n\n"  # Add separator
    
    return markdown

def find_toml_files(directory: str) -> List[str]:
    """Find all TOML files in the specified directory."""
    return glob.glob(f'{directory}/*.toml')

def sort_questions(questions: Dict[str, Question]) -> OrderedDict[str, Question]:
    """Sort questions by their ID."""
    def sort_key(id_question_pair):
        q_id = id_question_pair[0]
        return float(q_id) if q_id.replace('.', '', 1).isdigit() else q_id
        
    return OrderedDict(sorted(questions.items(), key=sort_key))

def process_files(file_paths: List[str]) -> OrderedDict[str, Question]:
    """Process all TOML files and return sorted questions."""
    all_questions: Dict[str, Question] = {}
    
    for file_path in file_paths:
        questions = load_toml_file(file_path)
        for question in questions:
            all_questions[question.id] = question
    
    return sort_questions(all_questions)

def generate_markdown(questions: OrderedDict[str, Question]) -> str:
    """Generate complete markdown content from questions."""
    markdown = "# The Larger Catechism\n\n"
    
    for question in questions.values():
        markdown += format_question(question)
    
    return markdown

def save_markdown(content: str, output_path: str) -> None:
    """Save markdown content to a file."""
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"Conversion complete. Markdown file created: {output_path}")

def main() -> None:
    """Main function to orchestrate the conversion process."""
    source_dir = 'src'
    output_file = 'larger-catechism.md'
    
    # Find TOML files
    toml_files = find_toml_files(source_dir)
    if not toml_files:
        print(f"No TOML files found in the {source_dir} directory.")
        return
    
    # Process files and generate markdown
    questions = process_files(toml_files)
    markdown_content = generate_markdown(questions)
    
    # Save the result
    save_markdown(markdown_content, output_file)

if __name__ == "__main__":
    main()