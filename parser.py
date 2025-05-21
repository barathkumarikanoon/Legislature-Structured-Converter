import xml.etree.ElementTree as ET
import re
import subprocess
import os

def convert_to_xml(pdf_path, base_name_of_file):
    # Derive output file name from input PDF
    output_xml_path = f"{base_name_of_file}.xml"

    try:
        # Build and run the command
        cmd = [
            "pdf2txt.py",
            "-A",
            "-t", "xml",
            "-o", output_xml_path,
            pdf_path
        ]

        subprocess.run(cmd, check=True)
        print(f"parse completed: {output_xml_path}")

    except subprocess.CalledProcessError as e:
        print(f"parse failed: {e}")



def is_header(font_size,x0,y0):
    if  0 <= x0 <= 500 and 750 <= y0 <= 1000 and font_size=="13.470":
        return True
    return False

def is_short_title(font_size,x0,y0):
    # if (0 <= x0 <= 150  or 450 <= x0 <= 600) and 0 <= y0 <=1000 and font_size == "10.830":
    if (0 <= x0 <= 125  or 475 <= x0 <= 600) and 0 <= y0 <=1000 and font_size == "10.830":
        return True
    return False

def preprocess_short_title(short_title):
    pattern = re.compile(r'^\d+\s+of\s+\d+$')
    cleaned_short_title = [title for title in short_title if title.strip() and not pattern.match(title.strip())]
    return cleaned_short_title


def extract_text_from_xml(xml_file,base_name_of_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    page_texts =""

    for page in root.findall(".//page"):
        page_id = page.attrib.get("id", "unknown")
        # print("____"+page_id+"____")
        combined_text=[]
        short_title = []
        for text_box in page.findall(".//textbox"):
            x0,y0,x1,y1= list(map(float, text_box.attrib["bbox"].split(",")))
            #original header
            short_title_status = False
            # short_title_text_line = ""
            line_text =""
            for textline in text_box.findall(".//textline"):
                
                for t in textline.findall(".//text"):
                    font_size = t.attrib.get("size")
                    if is_header(font_size,x0,y0):
                        continue

                    elif is_short_title(font_size,x0,y0):
                        short_title_status=True
                        if t.text:
                            line_text += t.text
                    
                    else:
                        if t.text:
                            line_text += t.text
            if short_title_status:
                short_title += line_text.replace("\n","").split(".")
            elif line_text != "":
                if line_text.strip():
                    combined_text.append(line_text.replace("\n"," ").strip())
        short_title = preprocess_short_title(short_title)
        for text in combined_text[1:]:
            # match = re.match(r"^(\d+\.)\s*(.*)", text, re.DOTALL)
            match = re.match(r"^(\d+\.)\s*(.)*", text, re.DOTALL)
            if match:
               number = match.group(1).strip()
               remain_text = match.group(2).strip()
               if len(short_title) >= 1:
                   title = short_title[0]
                   short_title.pop(0)
                   formatted = f"{number} {title}\n{remain_text.strip()}"
                   page_texts+=formatted
            
            else:
                page_texts += (text+"\n")

    with open(f"{base_name_of_file}.txt", "w") as file:
        file.write(page_texts)


if __name__ == "__main__":

    pdf_path = r'boilers act.pdf'
    base_name_of_file = os.path.splitext(os.path.basename(pdf_path))[0]
    convert_to_xml(pdf_path,base_name_of_file)

    xml_path = f"{base_name_of_file}.xml"
    extract_text_from_xml(xml_path,base_name_of_file)


