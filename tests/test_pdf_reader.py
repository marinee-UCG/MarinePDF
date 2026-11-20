from backend.ingestion.pdf_reader import clean_text, extract_section


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