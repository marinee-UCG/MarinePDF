import re
from dataclasses import dataclass
from pathlib import Path
import pymupdf

HANGUL_RE=re.compile(r"[\uAC00-\uD7A3\u1100-\u11FF\u3130-\u318F]+")
SECTION_RE = re.compile(r"^[A-Z]\d{5}$")
PAGE_NO_RE =re.compile(r"^\d+/\d+$")
MIN_PAGE_CHARS=50
ALNUM_RE=re.compile(r"[A-Za-z0-9]")

@dataclass
class Page():
    page_number:int
    text:str
    section_code:str | None
    section_title:str | None


def clean_text(raw:str) -> str:
    """REMOVE KOREAN,COLLAPSE WHITESPACE,DROP EMPTY LINES"""
    text=HANGUL_RE.sub("",raw)
    lines=text.splitlines()
    cleaned=[]
    for line in lines:
        line = " ".join(line.split())
        if ALNUM_RE.search(line) :
            cleaned.append(line)
    return "\n".join(cleaned)

def extract_section(raw:str) -> tuple[str | None, str | None]:
    text=clean_text(raw)
    lines=text.splitlines()
    header_lines=lines[:15]
    if "Section No." not in header_lines:
        return None,None
    label_index=header_lines.index("Section No.")
    code_index=label_index + 1
    if code_index >= len(header_lines) or not SECTION_RE.match(header_lines[code_index]):
        return None,None
    code=header_lines[code_index]
    title_start=0
    for j in range(label_index):
        if PAGE_NO_RE.match(header_lines[j]):
            title_start= j+1
            break
    title = " ".join(header_lines[title_start:label_index])
    return code,title

def read_pages(pdf_path:str | Path) ->list[Page]:
    pages=[]
    current_code= None
    current_title= None
    with pymupdf.open(pdf_path) as doc:
        for i,pdf_page in enumerate(doc):
            raw=pdf_page.get_text()
            code,title=extract_section(raw)
            if code:
                current_code,current_title=code,title
            text=clean_text(raw)
            if len(text) < MIN_PAGE_CHARS:
                continue
            page=Page(page_number=i+1,text=text,section_code=current_code,section_title=current_title)
            pages.append(page)
    return pages        
