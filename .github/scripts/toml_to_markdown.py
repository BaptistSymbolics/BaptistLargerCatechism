#!/usr/bin/env python3
"""
Convert all catechism TOML files in the src directory to a nicely formatted Markdown file.
"""
import toml
import os
import re
import glob
from collections import OrderedDict

def process_question(question_data):
    """Process a single question into markdown format."""
    q_id = question_data.get('id', '')
    question_text = question_data.get('question', '')
    sections = question_data.get('sections', [])
    
    # Start with the question in header format with 'Q.' prefix
    markdown = f"# Q. {q_id}: {question_text}\n\n"
    
    # Begin the answer with 'A:' prefix
    markdown += "A: "
    
    # Process all sections to create the full answer text with superscript references
    full_text = ""
    footnote_counter = 1
    footnotes = []
    
    # Check if first section starts an enumerated list
    is_enum_list = False
    list_item_pattern = re.compile(r'^(\d+)\.\s')
    
    # Count sections that start with a number followed by a period
    enum_sections = []
    for section in sections:
        section_text = section.get('text', '').strip()
        if section_text and list_item_pattern.match(section_text):
            enum_sections.append(True)
        elif section_text:
            enum_sections.append(False)
    
    # If a significant portion of non-empty sections start with numbers, treat as enumerated list
    if enum_sections and enum_sections.count(True) >= 3:
        is_enum_list = True
    
    # Process sections
    for i, section in enumerate(sections):
        section_text = section.get('text', '').strip()
        section_verses = section.get('verses', '')
        
        if not section_text:
            continue
            
        # Format enumerated list items
        if is_enum_list and list_item_pattern.match(section_text):
            # Extract the number from the start of the text
            match = list_item_pattern.match(section_text)
            list_num = match.group(1)
            
            # Replace the number at the start with blank for the full text
            text_without_number = list_item_pattern.sub('', section_text)
            
            # Add it as a list item with proper indentation if it's not the first item
            if full_text:
                full_text += "\n\n"  # Add spacing before list item
                
            full_text += f"{list_num}. {text_without_number}"
            
            # Add superscript
            if section_verses.strip():
                full_text += f"$^{{{footnote_counter}}}$"
                footnotes.append((footnote_counter, section_verses))
                footnote_counter += 1
        else:
            # Process regular sections
            if section_verses.strip():
                if full_text:
                    full_text += " "  # Add space between sections
                full_text += f"{section_text}$^{{{footnote_counter}}}$"
                footnotes.append((footnote_counter, section_verses))
                footnote_counter += 1
            else:
                if full_text:
                    full_text += " "  # Add space between sections
                full_text += section_text
    
    # Add the complete answer text
    markdown += full_text.strip() + "\n\n"
    
    # Add footnotes in a numbered list
    for number, verses in footnotes:
        if verses.strip():
            # Create a URL for BibleGateway search
            encoded_verses = verses.replace(' ', '+').replace(':', '%3A').replace(';', '%3B').replace(',', '%2C')
            bible_url = f"https://www.biblegateway.com/passage/?search={encoded_verses}&version=ESV"
            markdown += f"{number}. [{verses}]({bible_url})\n"
    
    markdown += "\n---\n\n"  # Add a separator between questions
    
    return markdown

def main():
    """
    Main function to process all TOML files and generate markdown.
    """
    # Find all TOML files in the src directory
    toml_files = glob.glob('src/*.toml')
    
    if not toml_files:
        print("No TOML files found in the src directory.")
        return
    
    # Dictionary to store all questions with their IDs as keys
    all_questions = OrderedDict()
    
    # Process each TOML file
    for toml_file in toml_files:
        try:
            with open(toml_file, 'r', encoding='utf-8') as file:
                question_data = toml.load(file)
                
                # Handle the case where the file contains a single question
                if 'id' in question_data and 'question' in question_data:
                    q_id = question_data.get('id', '')
                    all_questions[q_id] = question_data
                # Handle the case where the file contains multiple questions
                elif isinstance(question_data, list):
                    for question in question_data:
                        if 'id' in question and 'question' in question:
                            q_id = question.get('id', '')
                            all_questions[q_id] = question
        except Exception as e:
            print(f"Error processing file {toml_file}: {e}")
    
    # Sort questions by ID
    sorted_questions = OrderedDict(sorted(all_questions.items(), 
                                          key=lambda x: float(x[0]) if x[0].replace('.', '', 1).isdigit() else x[0]))
    
    # Create markdown content with title
    markdown = "# The Larger Catechism\n\n"
    
    # Process each question in order
    for q_id, question_data in sorted_questions.items():
        markdown += process_question(question_data)
    
    # Write markdown to file
    with open('larger-catechism.md', 'w', encoding='utf-8') as file:
        file.write(markdown)
    
    print("Conversion complete. Markdown file created: larger-catechism.md")

if __name__ == "__main__":
    main()