import pytest
from pathlib import Path
from backend.app.document_processing.loaders import TextLoader, get_loader_for_file

def test_text_loader(tmp_path):
    test_file = tmp_path / "sample.txt"
    content = "# Section 1: Intro\nThis is the introductory content for testing.\n\n# Section 2: Methods\nHere we describe experimental methodology."
    test_file.write_text(content, encoding="utf-8")

    loader = get_loader_for_file(test_file)
    pages = loader.load(test_file)

    assert len(pages) >= 2
    assert pages[0].page_number == 1
    assert "Section 1" in pages[0].text
    assert pages[1].page_number == 2
    assert "Section 2" in pages[1].text
    assert pages[0].metadata["file_type"] == "txt"

def test_empty_text_loader(tmp_path):
    test_file = tmp_path / "empty.txt"
    test_file.write_text("", encoding="utf-8")

    loader = TextLoader()
    pages = loader.load(test_file)
    assert len(pages) == 1
    assert pages[0].page_number == 1
