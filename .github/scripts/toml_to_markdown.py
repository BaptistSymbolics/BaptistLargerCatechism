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
    
    # Process sections differently if it's an enumerated list
    if is_enum_list:
        # For enumerated lists, process the non-list part first
        full_text = ""
        footnote_counter = 1
        footnotes = []
        
        # First, handle any text before the enumerated list
        for section in sections:
            section_text = section.get('text', '').strip()
            section_verses = section.get('verses', '')
            
            if not section_text:
                continue
                
            if not list_item_pattern.match(section_text):
                if section_verses.strip():
                    full_text += f"{section_text}$^{{{footnote_counter}}}$ "
                    footnotes.append((footnote_counter, section_verses))
                    footnote_counter += 1
                else:
                    full_text += f"{section_text} "
        
        # Add the non-list part
        if full_text:
            markdown += full_text.strip() + "\n\n"
        
        # Now handle the enumerated list items
        first_list_item = True
        for section in sections:
            section_text = section.get('text', '').strip()
            section_verses = section.get('verses', '')
            
            if not section_text:
                continue
                
            if list_item_pattern.match(section_text):
                match = list_item_pattern.match(section_text)
                list_num = match.group(1)
                text_without_number = list_item_pattern.sub('', section_text)
                
                # Add the list item
                if first_list_item:
                    first_list_item = False
                else:
                    markdown += "\n"
                    
                # Add the list item with its verse reference
                if section_verses.strip():
                    markdown += f"{list_num}. {text_without_number}$^{{{footnote_counter}}}$"
                    footnotes.append((footnote_counter, section_verses))
                    footnote_counter += 1
                else:
                    markdown += f"{list_num}. {text_without_number}"
        
        # Add two newlines after the list
        markdown += "\n\n"
                
        # Add footnotes in a numbered list
        for number, verses in footnotes:
            if verses.strip():
                # Create a URL for BibleGateway search
                encoded_verses = verses.replace(' ', '+').replace(':', '%3A').replace(';', '%3B').replace(',', '%2C')
                bible_url = f"https://www.biblegateway.com/passage/?search={encoded_verses}&version=ESV"
                markdown += f"{number}. [{verses}]({bible_url})\n"
    
    else:
        # Process regular sections (non-enumerated list)
        full_text = ""
        footnote_counter = 1
        footnotes = []
        
        for section in sections:
            section_text = section.get('text', '').strip()
            section_verses = section.get('verses', '')
            
            if not section_text:
                continue
                
            if section_verses.strip():
                full_text += f"{section_text}$^{{{footnote_counter}}}$ "
                footnotes.append((footnote_counter, section_verses))
                footnote_counter += 1
            else:
                full_text += f"{section_text} "
        
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