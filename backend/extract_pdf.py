import fitz

doc = fitz.open(r"c:\Users\lekka\OneDrive\Desktop\smart-underwriter\TATHLIP21255V022021_2020-2021.pdf")
text = ""
# Read first 10 pages for a start
for i in range(min(10, len(doc))):
    text += f"--- Page {i+1} ---\n"
    text += doc[i].get_text()

with open(r"c:\Users\lekka\OneDrive\Desktop\smart-underwriter\backend\pdf_text.txt", "w", encoding="utf-8") as f:
    f.write(text)
print(f"Extracted {len(text)} characters.")
