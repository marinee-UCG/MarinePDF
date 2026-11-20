from backend.ingestion.pdf_reader import clean_text, extract_section
from backend.ingestion.chunker import chunk_page
from backend.ingestion.pdf_reader import Page


def test_clean_text_removes_korean():
    raw = "분해 절차 Loosening Procedure"
    assert clean_text(raw) == "Loosening Procedure"


def test_clean_text_drops_empty_lines_and_collapses_spaces():
    assert clean_text("일반 사항\n  Engine   Stopping  \n\n") == "Engine Stopping"


def test_extract_section_from_header():
    raw = "All type\nPage\n1/2\nNormal Operation\nEngine Stopping\nSection No.\nO02700\nRev.\n1A\nHYUNDAI HEAVY INDUSTRIES"

    assert extract_section(raw) == ("O02700", "Normal Operation Engine Stopping")


def test_extract_section_missing_returns_none():
    assert extract_section("HYUNDAI\nINSTRUCTION BOOK\nVOLUME") == (None, None)


def test_clean_text_drops_punctuation_only_lines():
    raw = ".\n( ) .\n,\nClean seat and threads.\n250 bar"
    assert clean_text(raw) == "Clean seat and threads.\n250 bar"


def test_short_page_is_single_chunk():
    page=Page(5,"Short text.","G00100","Contents")
    assert [c.content for c in chunk_page(page)] == ["Short text."]

def test_long_page_split_with_limits_and_overlap():
    text=" ".join(f"Sentence number {i}." for i in range(200))
    chunks=chunk_page(Page(1,text,None,None),chunk_size=800,overlap=150)
    assert len(chunks) > 1
    assert all(len(c.content) <= 800 for c in chunks)
    assert chunks[0].content[-50:] in chunks[1].content

def test_metadata_copied_to_every_chunk():
    page=Page(42,"x. "*1000,"M31000","Piston")
    assert {(c.page_number,c.section_code) for c in chunk_page(page)} == {(42,"M31000")}
    