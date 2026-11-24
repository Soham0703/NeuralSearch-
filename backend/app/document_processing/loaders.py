import os
import re
from pathlib import Path
from typing import List, Dict, Any
import pypdf
import docx

class DocumentPage:
    def __init__(self, page_number: int, text: str, metadata: Dict[str, Any] = None):
        self.page_number = page_number
        self.text = text
        self.metadata = metadata or {}

class BaseLoader:
    def load(self, file_path: Path) -> List[DocumentPage]:
        raise NotImplementedError

class PDFLoader(BaseLoader):
    """Loads PDF documents preserving exact page boundaries and page numbers."""
    def load(self, file_path: Path) -> List[DocumentPage]:
        pages: List[DocumentPage] = []
        reader = pypdf.PdfReader(str(file_path))
        
        for idx, page in enumerate(reader.pages):
            page_num = idx + 1
            raw_text = page.extract_text() or ""
            # Clean up whitespace while preserving paragraphs
            clean_text = re.sub(r"[ \t]+", " ", raw_text)
            clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()
            
            if clean_text:
                pages.append(DocumentPage(
                    page_number=page_num,
                    text=clean_text,
                    metadata={"total_pages": len(reader.pages), "file_type": "pdf"}
                ))
        
        # If no extractable text found, return single placeholder page
        if not pages:
            pages.append(DocumentPage(
                page_number=1,
                text="[Document contained scanned or empty pages with no extractable text]",
                metadata={"total_pages": len(reader.pages), "file_type": "pdf"}
            ))
            
        return pages

class DocxLoader(BaseLoader):
    """Loads DOCX documents and segments text into logical pages (approx. 500 words per page)."""
    def load(self, file_path: Path) -> List[DocumentPage]:
        doc = docx.Document(str(file_path))
        full_text_blocks: List[str] = []
        
        # Extract paragraphs
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                full_text_blocks.append(text)
                
        # Extract tables
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    table_rows.append(row_text)
            if table_rows:
                full_text_blocks.append("\n".join(table_rows))
                
        # Segment into logical pages based on word count (~400 words per page)
        words_per_page = 400
        pages: List[DocumentPage] = []
        current_page_blocks = []
        current_word_count = 0
        current_page_num = 1
        
        for block in full_text_blocks:
            block_words = len(block.split())
            if current_word_count + block_words > words_per_page and current_page_blocks:
                pages.append(DocumentPage(
                    page_number=current_page_num,
                    text="\n\n".join(current_page_blocks),
                    metadata={"file_type": "docx"}
                ))
                current_page_num += 1
                current_page_blocks = [block]
                current_word_count = block_words
            else:
                current_page_blocks.append(block)
                current_word_count += block_words
                
        if current_page_blocks:
            pages.append(DocumentPage(
                page_number=current_page_num,
                text="\n\n".join(current_page_blocks),
                metadata={"file_type": "docx"}
            ))
            
        if not pages:
            pages.append(DocumentPage(
                page_number=1,
                text="[Empty document]",
                metadata={"file_type": "docx"}
            ))
            
        # Update total pages in metadata
        total_p = len(pages)
        for p in pages:
            p.metadata["total_pages"] = total_p
            
        return pages

class TextLoader(BaseLoader):
    """Loads plain text / markdown files, segmenting into pages at headings or character budgets."""
    def load(self, file_path: Path) -> List[DocumentPage]:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
            
        # Segment into logical pages (approx 2000 chars or at Markdown major headings #)
        sections = re.split(r"(?=\n#+ )", content)
        if len(sections) <= 1:
            # Segment by approx 2000 characters
            chars_per_page = 2000
            sections = [content[i:i + chars_per_page] for i in range(0, len(content), chars_per_page)]
            
        pages: List[DocumentPage] = []
        for idx, sec in enumerate(sections):
            sec_text = sec.strip()
            if sec_text:
                pages.append(DocumentPage(
                    page_number=idx + 1,
                    text=sec_text,
                    metadata={"file_type": "txt", "total_pages": len(sections)}
                ))
                
        if not pages:
            pages.append(DocumentPage(
                page_number=1,
                text="[Empty document]",
                metadata={"file_type": "txt", "total_pages": 1}
            ))
            
        return pages

def get_loader_for_file(file_path: Path) -> BaseLoader:
    suffix = file_path.suffix.lower()
    if suffix == ".pdf":
        return PDFLoader()
    elif suffix in [".docx", ".doc"]:
        return DocxLoader()
    elif suffix in [".txt", ".md", ".csv", ".json"]:
        return TextLoader()
    else:
        # Fallback to TextLoader
        return TextLoader()
