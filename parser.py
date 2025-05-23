import xml.etree.ElementTree as ET
import re
import subprocess
import os

# --- PDF to XML Conversion ---#

def convert_to_xml(pdf_path, base_name_of_file):
    output_xml_path = f"{base_name_of_file}.xml"
    cmd = [
        "pdf2txt.py",
        "-A",
        "-t", "xml",
        "-o", output_xml_path,
        pdf_path
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"[✔] Parse completed: {output_xml_path}")
    except subprocess.CalledProcessError as e:
        print(f"[✖] Parse failed: {e}")

# --- Header & Short Title Identification --- #

def is_header(font_size, x0, y0):
    return 0 <= x0 <= 700 and 750 <= y0 <= 1000 and font_size == "13.470"

def is_short_title(font_size, x0, y0):
    return (0 <= x0 <= 125 or 475 <= x0 <= 700) and 0 <= y0 <= 1000 and font_size == "10.830"

def preprocess_short_titles(titles):
    pattern = re.compile(r'^\d+\s+of\s+\d+\.$')         # to exclude 16 of 2024,... like reference mentioned from the short title space
    return [title for title in titles if title.strip() and not pattern.match(title.strip())]

# --- XML Text Extraction --- #

def extract_text_from_xml(xml_path, base_name):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    output_text = []

    for page in root.findall(".//page"):
        text_boxes = get_sorted_textboxes(page)
        combined_lines, short_titles = extract_lines_and_titles(text_boxes)
        short_titles = preprocess_short_titles(short_titles)
        output_text.extend(build_structured_output(combined_lines, short_titles))

    write_output_file(base_name, output_text)
    print(f"[✔] Output written to {base_name}.txt")

# --- Helper Functions --- #

# getting sorted textboxes to extract text in the order of arrangement
def get_sorted_textboxes(page):
    def parse_bbox(textbox):
        x0, y0, x1, y1 = map(float, textbox.attrib["bbox"].split(","))
        return x0, y0, x1, y1
    
    return    sorted(page.findall(".//textbox"),
        key=lambda tb: (
            -float(parse_bbox(tb)[1]),  # y0: top to bottom (higher y lower)
           float(parse_bbox(tb)[0]), #,   # x0: left to right
            -float(parse_bbox(tb)[3]),  # y1: optional secondary vertical order
            float(parse_bbox(tb)[2])    # x1: optional secondary horizontal order
         )
    )

# to extract each textlines and short titles
def extract_lines_and_titles(text_boxes):
    combined_lines = []
    short_titles = []

    for box in text_boxes:
        x0, y0, x1, y1 = map(float, box.attrib["bbox"].split(","))
        line_text, is_short = extract_text_from_box(box, x0, y0)

        if is_short:
            short_titles += [part.strip() for part in re.split(r'\.(?=\w)', line_text.replace("\n", "")) if part.strip()]
        elif line_text.strip():
            combined_lines.append(line_text.replace("\n", " ").strip())

    return combined_lines, short_titles

# to extract text from each lines
def extract_text_from_box(box, x0, y0):
    line_text = ""
    is_short = False

    for textline in box.findall(".//textline"):
        for t in textline.findall(".//text"):
            font_size = t.attrib.get("size")
            content = t.text or ""

            if is_header(font_size, x0, y0):
                continue
            elif is_short_title(font_size, x0, y0):
                is_short = True
            line_text += content

    return line_text, is_short

# to fit the short title in the corresponding space.
def build_structured_output(lines, short_titles):
    structured = []
    for text in lines[1:]:  # Optionally skip the first line
        #this regex is to fit the the short title in the respective places. like when it detect 1. Text ==> 1. short title \n Text 
        match = re.match(r"^(\d+\.)\s*(.*)", text, re.DOTALL)
        if match:
            number, remaining = match.groups()
            if short_titles:
                title = short_titles.pop(0)
                structured.append(f"{number} {title}\n{remaining.strip()}")
            else:
                structured.append(text)
        else:
            structured.append(text)
    return structured

# write the structured text to the txt file
def write_output_file(base_name, lines):
    with open(f"{base_name}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

# --- Main --- #

if __name__ == "__main__":
    pdf_path = r'boilers act.pdf'  # 👈 Replace with your PDF path
    base_name_of_file = os.path.splitext(os.path.basename(pdf_path))[0]
    convert_to_xml(pdf_path, base_name_of_file)

    xml_path = f"{base_name_of_file}.xml"
    extract_text_from_xml(xml_path, base_name_of_file)
