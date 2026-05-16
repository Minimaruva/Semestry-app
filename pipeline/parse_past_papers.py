import pdfplumber
import os
import re

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct path relative to the script location
paper = "COMP3223-2019-2020.pdf"
module = "COMP3223"
pdf_path = os.path.join(script_dir, "data", "raw", "modules", module, paper)

def extract_text_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = ""
        for page in pdf.pages:
            text = page.extract_text()
            full_text += text + "\n"
    return full_text

def extract_questions_from_text(text):
    '''
    Use regular expressions to detect question patterns in the text 
    '''
    # Format: {"question_number": {"part a": ["question text", marks], ...}}
    questions = {}
    
    expr = r'(?i)\b(?:Question|Q)\s*\d+'
    
    test_questions = []

    matches = list(re.finditer(expr, text))

    for i, match in enumerate(matches):
        header = match.group()
        # The question starts after header, and ends before the next question header (or end of text)
        # this avoids any complex regexes
        start_idx = match.end()
    
        # The content ends where the NEXT match starts. 
        # for last question go to the eos
        if i + 1 < len(matches):
            end_idx = matches[i + 1].start()
        else:
            end_idx = len(text)
        
        content = text[start_idx:end_idx].strip()
        test_questions.append((header, content))
    
    return test_questions

if __name__ == "__main__":
    text = extract_text_from_pdf(pdf_path)
    # print(text) 
    questions = extract_questions_from_text(text)
    for q, c in questions:
        print(f"Header: {q}")
        print(f"Content: {c}\n---")
