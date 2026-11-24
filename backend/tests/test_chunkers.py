import pytest
from backend.app.document_processing.loaders import DocumentPage
from backend.app.document_processing.chunkers import (
    RecursiveCharacterChunker, PageBasedChunker, SemanticChunker, get_chunker
)

def test_recursive_chunker():
    pages = [
        DocumentPage(
            page_number=1,
            text="First paragraph of section one with detailed analysis. Second paragraph detailing empirical findings and observations."
        ),
        DocumentPage(
            page_number=2,
            text="Second page begins here with architectural specifications. Concluding remarks on latency and throughput."
        )
    ]

    chunker = RecursiveCharacterChunker(chunk_size=60, chunk_overlap=15)
    chunks = chunker.chunk_pages(pages)

    assert len(chunks) > 0
    # Every chunk must preserve correct page_number
    for c in chunks:
        assert c.page_number in [1, 2]
        assert len(c.text) > 0
        assert c.token_count > 0

def test_page_based_chunker():
    pages = [
        DocumentPage(page_number=1, text="Short page one text."),
        DocumentPage(page_number=2, text="Short page two text.")
    ]

    chunker = PageBasedChunker(max_page_chunk_size=200, overlap=20)
    chunks = chunker.chunk_pages(pages)

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 2
    assert chunks[0].metadata["is_full_page"] is True

def test_semantic_chunker():
    pages = [
        DocumentPage(page_number=1, text="Paragraph A.\n\nParagraph B.\n\nParagraph C.")
    ]
    chunker = SemanticChunker(target_size=25, overlap=5)
    chunks = chunker.chunk_pages(pages)
    assert len(chunks) >= 2
