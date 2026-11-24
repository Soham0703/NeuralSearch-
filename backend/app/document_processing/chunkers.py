import re
from typing import List, Dict, Any, Optional
from backend.app.document_processing.loaders import DocumentPage

class Chunk:
    def __init__(
        self,
        text: str,
        chunk_index: int,
        page_number: int,
        start_char: int,
        end_char: int,
        token_count: int,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.text = text
        self.chunk_index = chunk_index
        self.page_number = page_number
        self.start_char = start_char
        self.end_char = end_char
        self.token_count = token_count
        self.metadata = metadata or {}

class BaseChunker:
    def chunk_pages(self, pages: List[DocumentPage]) -> List[Chunk]:
        raise NotImplementedError

class RecursiveCharacterChunker(BaseChunker):
    """
    Enterprise hierarchical text chunker that attempts splitting on paragraphs,
    then sentences, then clauses, preserving page-level attribution and overlap.
    """
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        if not separators:
            return list(text)
            
        separator = separators[0]
        if separator == "":
            return list(text)
            
        splits = text.split(separator)
        result = []
        for s in splits:
            if s:
                result.append(s)
        return result

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for split in splits:
            split_len = len(split) + (len(separator) if current_chunk else 0)
            if current_length + split_len > self.chunk_size and current_chunk:
                merged = separator.join(current_chunk)
                chunks.append(merged)
                
                # Keep overlap from the end of current_chunk
                overlap_acc = []
                overlap_len = 0
                for item in reversed(current_chunk):
                    if overlap_len + len(item) <= self.chunk_overlap:
                        overlap_acc.insert(0, item)
                        overlap_len += len(item)
                    else:
                        break
                        
                current_chunk = overlap_acc + [split]
                current_length = sum(len(x) for x in current_chunk) + len(separator) * (len(current_chunk) - 1)
            else:
                current_chunk.append(split)
                current_length += split_len

        if current_chunk:
            chunks.append(separator.join(current_chunk))

        return chunks

    def chunk_pages(self, pages: List[DocumentPage]) -> List[Chunk]:
        all_chunks: List[Chunk] = []
        global_chunk_idx = 0

        for page in pages:
            page_text = page.text
            page_num = page.page_number
            
            # Recursive split on this page
            splits = self._recursive_split(page_text, self.separators)
            merged_texts = self._merge_splits(splits, separator=" ")
            
            char_offset = 0
            for text_chunk in merged_texts:
                clean_chunk = text_chunk.strip()
                if not clean_chunk:
                    continue
                    
                start_char = page_text.find(clean_chunk[:30], char_offset)
                if start_char == -1:
                    start_char = char_offset
                end_char = start_char + len(clean_chunk)
                char_offset = end_char
                
                token_est = max(1, len(clean_chunk) // 4)
                
                all_chunks.append(Chunk(
                    text=clean_chunk,
                    chunk_index=global_chunk_idx,
                    page_number=page_num,
                    start_char=start_char,
                    end_char=end_char,
                    token_count=token_est,
                    metadata={"strategy": "recursive", "page": page_num}
                ))
                global_chunk_idx += 1

        return all_chunks

    def _recursive_split(self, text: str, separators: List[str]) -> List[str]:
        final_pieces = []
        separator = separators[-1]
        
        for sep in separators:
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                break
                
        splits = text.split(separator) if separator != "" else list(text)
        
        for s in splits:
            if len(s) < self.chunk_size:
                final_pieces.append(s)
            else:
                next_separators = separators[separators.index(separator) + 1:] if separator in separators else []
                if next_separators:
                    final_pieces.extend(self._recursive_split(s, next_separators))
                else:
                    final_pieces.append(s)
                    
        return final_pieces

class PageBasedChunker(BaseChunker):
    """
    Chunker that treats each page as a primary unit, splitting only when
    a single page exceeds max chunk threshold. Preserves exact page boundaries.
    """
    def __init__(self, max_page_chunk_size: int = 800, overlap: int = 150):
        self.max_page_chunk_size = max_page_chunk_size
        self.overlap = overlap

    def chunk_pages(self, pages: List[DocumentPage]) -> List[Chunk]:
        all_chunks: List[Chunk] = []
        global_chunk_idx = 0

        for page in pages:
            text = page.text.strip()
            page_num = page.page_number
            
            if len(text) <= self.max_page_chunk_size:
                # Page fits entirely in one chunk
                all_chunks.append(Chunk(
                    text=text,
                    chunk_index=global_chunk_idx,
                    page_number=page_num,
                    start_char=0,
                    end_char=len(text),
                    token_count=max(1, len(text) // 4),
                    metadata={"strategy": "page_based", "page": page_num, "is_full_page": True}
                ))
                global_chunk_idx += 1
            else:
                # Sub-chunk the page with overlap
                start = 0
                while start < len(text):
                    end = min(start + self.max_page_chunk_size, len(text))
                    # Align to sentence boundary if possible
                    if end < len(text):
                        boundary = text.rfind(". ", start, end)
                        if boundary != -1 and boundary > start + (self.max_page_chunk_size // 2):
                            end = boundary + 1
                            
                    chunk_text = text[start:end].strip()
                    if chunk_text:
                        all_chunks.append(Chunk(
                            text=chunk_text,
                            chunk_index=global_chunk_idx,
                            page_number=page_num,
                            start_char=start,
                            end_char=end,
                            token_count=max(1, len(chunk_text) // 4),
                            metadata={"strategy": "page_based", "page": page_num, "is_full_page": False}
                        ))
                        global_chunk_idx += 1
                        
                    start = end - self.overlap
                    if start >= len(text) - self.overlap:
                        break

        return all_chunks

class SemanticChunker(BaseChunker):
    """
    Splits text along semantic breaks: double newlines, headings, and thematic boundaries.
    """
    def __init__(self, target_size: int = 600, overlap: int = 100):
        self.target_size = target_size
        self.overlap = overlap

    def chunk_pages(self, pages: List[DocumentPage]) -> List[Chunk]:
        all_chunks: List[Chunk] = []
        global_chunk_idx = 0

        for page in pages:
            text = page.text.strip()
            page_num = page.page_number
            # Split by double newline or numbered headings
            paragraphs = re.split(r"\n\s*\n|(?<=\.)\s+(?=[A-Z0-9]\.\s+)", text)
            
            current_chunk_paras = []
            current_len = 0
            
            for p in paragraphs:
                p_clean = p.strip()
                if not p_clean:
                    continue
                if current_len + len(p_clean) > self.target_size and current_chunk_paras:
                    merged = "\n\n".join(current_chunk_paras)
                    all_chunks.append(Chunk(
                        text=merged,
                        chunk_index=global_chunk_idx,
                        page_number=page_num,
                        start_char=0,
                        end_char=len(merged),
                        token_count=max(1, len(merged) // 4),
                        metadata={"strategy": "semantic", "page": page_num}
                    ))
                    global_chunk_idx += 1
                    current_chunk_paras = [p_clean]
                    current_len = len(p_clean)
                else:
                    current_chunk_paras.append(p_clean)
                    current_len += len(p_clean)
                    
            if current_chunk_paras:
                merged = "\n\n".join(current_chunk_paras)
                all_chunks.append(Chunk(
                    text=merged,
                    chunk_index=global_chunk_idx,
                    page_number=page_num,
                    start_char=0,
                    end_char=len(merged),
                    token_count=max(1, len(merged) // 4),
                    metadata={"strategy": "semantic", "page": page_num}
                ))
                global_chunk_idx += 1

        return all_chunks

def get_chunker(strategy: str = "recursive", chunk_size: int = 500, chunk_overlap: int = 100) -> BaseChunker:
    strategy_clean = (strategy or "recursive").lower()
    if strategy_clean == "page_based":
        return PageBasedChunker(max_page_chunk_size=chunk_size, overlap=chunk_overlap)
    elif strategy_clean == "semantic":
        return SemanticChunker(target_size=chunk_size, overlap=chunk_overlap)
    else:
        return RecursiveCharacterChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
