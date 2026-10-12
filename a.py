def chunk_text(
    text: str,
    chunk_size: int = config.CHUNK_SIZE,
    overlap: int = config.CHUNK_OVERLAP,
) -> list[str]:
    """Split text into fixed-size chunks with overlap."""
    text = text.strip()
    if not text:
        return []
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
 
    step = chunk_size - overlap
    chunks = [text[i:i + chunk_size].strip() for i in range(0, len(text), step)]
    return [c for c in chunks if c]
