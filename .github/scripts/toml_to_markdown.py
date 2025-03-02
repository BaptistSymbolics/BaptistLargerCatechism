#!/usr/bin/env python3
"""
Convert all catechism TOML files in the src directory to a nicely formatted Markdown file.
"""
import toml
import os
import re
import glob
from collections import OrderedDict

def format_verse_references(verses_list):
    """Format all verse references into a single table based on total reference count."""
    # Flatten all verse references
    all_refs = []
    for verses in verses_list:
        if verses:
            all_refs.extend([ref.strip() for ref in verses.split(';')])
    
    # If few references, return without a table
    if len(all_refs) < 6:
        return None
    
    # Determine column count
    if len(all_refs) <= 15:
        cols = 2
    elif len(all_refs) <= 25:
        cols = 3
    else:
        cols = 4
    
    # Calculate rows needed
    rows = (len(all_refs) + cols - 1) // cols
    
    # Build table
    table = "| " + " | ".join(["References"] * cols) + " |\n"
    table += "| " + " | ".join(["---"] * cols) + " |\n"
    
    # Fill table with references
    for i in range(rows):
        row_cells = []
        for j in range(cols):
            idx = i + j * rows
            if idx < len(all_refs):
                row_cells.append(all_refs[idx])
            else:
                row_cells.append("")
        table += "| " + " | ".join(row_cells) + " |\n"
    
    return table

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
    all_verses = []
    
    for section in sections:
        section_text = section.get('text', '')
        section_verses = section.get('verses', '')
        
        # Only add superscript and create footnote if verses exist
        if section_text:
            if section_verses.strip():
                # Add superscript footnote number to the end of section text
                full_text += f"{section_text}$^{{{footnote_counter}}}$ "
                footnotes.append((footnote_counter, section_verses))
                all_verses.append(section_verses)
                footnote_counter += 1
            else:
                # Just add the text without a footnote if no verses
                full_text += f"{section_text} "
    
    # Add the complete answer text
    markdown += full_text.strip() + "\n\n"
    
    # Create table for all verse references if needed
    verse_table = format_verse_references(all_verses)
    
    # Add footnotes in a numbered list
    for number, verses in footnotes:
        if verses.strip():
            # Create a URL for BibleGateway search
            encoded_verses = verses.replace(' ', '+').replace(':', '%3A').replace(';', '%3B').replace(',', '%2C')
            bible_url = f"https://www.biblegateway.com/passage/?search={encoded_verses}&version=ESV"
            
            # Make the verses themselves the hyperlink
            markdown += f"{number}. [{verses}]({bible_url})\n"
    
    # Add the table of all verse references if applicable
    if verse_table:
        markdown += "\n**All Scripture References:**\n\n"
        markdown += verse_table
    
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