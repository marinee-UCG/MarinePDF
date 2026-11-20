from backend.ingestion.pdf_reader import Page
from dataclasses import dataclass


@dataclass
class TextChunk():
    page_number:int
    section_code:str | None
    section_title:str | None
    content:str

def _find_cut(window:str,chunk_size:int) ->int:
    min_cut=chunk_size // 2
    cut=window.rfind("\n")
    if cut >= min_cut:
        return cut
    else:
        cut=window.rfind(". ")
        if cut >= min_cut:
            return cut + 1
        cut=window.rfind(" ")
        if cut >= min_cut:
            return cut
    return chunk_size

def chunk_page(page:Page,chunk_size:int = 800,overlap:int=150) -> list[TextChunk]:
    text=page.text
    chunks=[]
    start=0
    while start < len(text):
        if len(text) - start <= chunk_size:
            piece=text[start:]
            cut=len(text) - start
        else:
            window=text[start:start + chunk_size]
            cut=_find_cut(window,chunk_size)
            piece=window[:cut]
        piece=piece.strip()
        if piece:
            chunks.append(TextChunk(page.page_number,page.section_code,page.section_title,content=piece))
        if start + cut >= len(text):
            break
        start=start + cut -overlap
    return chunks

def chunk_pages(pages:list[Page],chunk_size:int = 800, overlap:int=150) ->list[TextChunk]:
    all_chunks=[]
    for page in pages:
        chunked=chunk_page(page,chunk_size,overlap)
        all_chunks.extend(chunked)
    return all_chunks