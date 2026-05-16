import pdfplumber
import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
# Construct path relative to the script location
paper = "COMP3223-2019-2020.pdf"
module = "COMP3223"
pdf_path = os.path.join(script_dir, "data", "raw", "modules", module, paper)

if __name__ == "__main__":
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            print(text)
