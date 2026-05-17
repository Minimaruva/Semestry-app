import pdfplumber
import os
import re
import json

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct path relative to the script location
paper = "COMP3223-2019-2020.pdf"
module = "COMP3223"
pdf_path = os.path.join(script_dir, "data", "raw", "modules", module, paper)
output_dir = os.path.join(script_dir, "data", "processed", module, paper.replace(".pdf", ""))

# ── Patterns ────────────────────────────────────────
QUESTION_RE = r'(?i)\b(?:Question|Q)\s*\d+'
# Text-level: matches (a),(b),... and (i),(ii),... at start of line
PART_RE     = re.compile(r'^\(?([a-z])\)\.?', re.MULTILINE)
SUBPART_RE  = re.compile(r'^\(?([ivxIVX]+)\)\.?', re.MULTILINE)
MARKS_RE    = re.compile(r'\[(\d+)\s*marks?\]', re.IGNORECASE)
# Word-level: matches standalone tokens like (a), (ii) from pdfplumber extract_words()
SECTION_WORD_RE = re.compile(r'^\(([a-z]|i{1,3}|iv|vi{0,3}|ix|x{1,3})\)$', re.IGNORECASE)
RESOLUTION  = 500

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
    Extract both text and coordinates 
    '''    
    questions = []

    matches = list(re.finditer(QUESTION_RE, text))

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
        questions.append((header, content))
    
    return questions


def extract_parts_from_content(content):
    '''
    Split question content into parts and subparts: (a),(b),... and (i),(ii),...
    Tries PART_RE first; falls back to SUBPART_RE if no lettered parts found.
    Returns list of (part_label, part_text, marks) tuples.
    '''
    matches = list(re.finditer(PART_RE, content))
 
    # Fall back to subpart regex if no (a),(b)... found — some papers use (i),(ii),...
    if not matches:
        matches = list(re.finditer(SUBPART_RE, content))
 
    parts = []
    for i, match in enumerate(matches):
        label     = match.group(1)
        start_idx = match.end()
        end_idx   = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        part_text = content[start_idx:end_idx].strip()
 
        marks_match = MARKS_RE.search(part_text)
        marks = int(marks_match.group(1)) if marks_match else None
 
        parts.append((label, part_text, marks))
 
    return parts
 
 
def find_question_page_ranges(pdf_path):
    '''
    Scan each page for question headers to determine which pages each question spans.
    Returns dict: { "Question 1": [page_indices...] }
    '''
    question_pages   = {}
    current_question = None
 
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text  = page.extract_text() or ""
            match = re.search(QUESTION_RE, text)
 
            if match:
                current_question = match.group().strip()
                question_pages[current_question] = []
 
            if current_question:
                question_pages[current_question].append(page_num)
 
    return question_pages
 
 
def find_parts_with_marks_on_page(page):
    '''
    Find (part_label, y_top, y_bottom) for each part/subpart on a page.
    y_top    = top of the (a)/(i) label word
    y_bottom = bottom of the [X marks] token nearest below it
    Also returns question_header_y if a "Question N" header is on this page.
    Covers both lettered parts (a),(b) and roman numeral subparts (i),(ii).
    '''
    words = page.extract_words()

    marks_positions = []
    for word in words:
        if re.match(r'^\[\d+', word['text']):
            marks_positions.append(word['bottom'])

    question_header_y = None
    for i, word in enumerate(words):
        if re.match(r'(?i)^Question$', word['text']) and i + 1 < len(words):
            if re.match(r'^\d+$', words[i + 1]['text']):
                question_header_y = word['top']
                break

    # Group words by line (same top y within 3px tolerance)
    lines = {}
    for word in words:
        key = round(word['top'] / 3) * 3
        if key not in lines:
            lines[key] = []
        lines[key].append(word)

    # Only match section labels that are the FIRST word on their line
    part_positions = []
    for y_key, line_words in lines.items():
        first_word = min(line_words, key=lambda w: w['x0'])
        m = SECTION_WORD_RE.match(first_word['text'])
        if m:
            part_positions.append((m.group(1), first_word['top']))

    result = []
    for part_label, part_y in part_positions:
        marks_below = [m for m in marks_positions if m > part_y]
        if marks_below:
            y_bottom = min(marks_below)
            result.append((part_label, part_y, y_bottom))

    return result, question_header_y
 
 
def extract_question_screenshots_from_questions(pdf_path, question_pages, output_dir):
    '''
    For each question/part:
    - First section of each question: crop extended up to include header/preamble
    - All other parts: crop from section label down to [marks] bottom
    '''
    os.makedirs(output_dir, exist_ok=True)
    manifest = {}
 
    with pdfplumber.open(pdf_path) as pdf:
        for question, page_indices in question_pages.items():
            safe_label  = re.sub(r'\s+', '_', question)
            saved_paths = []
            first_section_saved = False
 
            for page_num in page_indices:
                page  = pdf.pages[page_num]
                parts, question_header_y = find_parts_with_marks_on_page(page)
 
                for part_label, y_top, y_bottom in parts:
                    # First section of the question: extend crop up to include header + preamble
                    if not first_section_saved and question_header_y is not None and question_header_y < y_top:
                        y_top = question_header_y
                    first_section_saved = True
 
                    bbox    = (0, y_top, page.width, y_bottom)
                    cropped = page.crop(bbox)
 
                    filename   = f"{safe_label}_part_{part_label}_p{page_num + 1}.png"
                    image_path = os.path.join(output_dir, filename)
                    cropped.to_image(resolution=RESOLUTION).save(image_path)
                    saved_paths.append(image_path)
 
            manifest[safe_label] = {
                'question':    question,
                'pages':       [p + 1 for p in page_indices],
                'image_paths': saved_paths,
            }
 
    return manifest
 
 
if __name__ == "__main__":
    text      = extract_text_from_pdf(pdf_path)
    questions = extract_questions_from_text(text)
 
    question_pages = find_question_page_ranges(pdf_path)
    img_manifest   = extract_question_screenshots_from_questions(pdf_path, question_pages, output_dir)
 
    full_manifest = {}
    for header, content in questions:
        safe_label = re.sub(r'\s+', '_', header.strip())
        parts      = extract_parts_from_content(content)
 
        full_manifest[safe_label] = {
            **img_manifest.get(safe_label, {}),
            'text':  content,
            'parts': {
                label: {'text': part_text, 'marks': marks}
                for label, part_text, marks in parts
            }
        }
 
        print(f"Header: {header}")
        print(f"Pages:  {full_manifest[safe_label].get('pages')}")
        print(f"Images: {full_manifest[safe_label].get('image_paths')}")
        for label, part_text, marks in parts:
            print(f"  Part ({label}) [{marks} marks]: {part_text[:80]}...")
        print("---")
 
    manifest_path = os.path.join(output_dir, "manifest.json")
    os.makedirs(output_dir, exist_ok=True)
    with open(manifest_path, "w") as f:
        json.dump(full_manifest, f, indent=2)
    print(f"\nManifest saved to {manifest_path}")