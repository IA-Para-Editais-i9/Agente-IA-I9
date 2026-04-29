import tiktoken
from typing import List

def chunk_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
    encoding_name: str = "cl100k_base"
) -> List[str]:
    # divide um texto em chunks com sobreposição.
    
       if not text:
        return []
    
    enc = tiktoken.get_encoding(encoding_name)
    tokens = enc.encode(text)
    
    chunks = []
    start = 0
    step = chunk_size - overlap
    
    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        start += step
    
    return chunks


def chunk_markdown_table(
    markdown: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[str]:

    # p mdcom tabelas
    # p n quebrar tabelas no meio

    return chunk_text(markdown, chunk_size, overlap)
