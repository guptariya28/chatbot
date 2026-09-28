# 📍 FILE: app.py | Replace your current _format_sources function completely

def _format_sources(sources: list[dict]) -> list[dict]:
    """🟢 PRODUCTION SOURCE FORMATTER:
    Transforms raw vector document structures into clean, clickable UI target payloads 
    displaying ONLY the clean filename with 100% correct spelling syntax.
    """
    formatted = []
    seen_sources = set()  # 🟢 Correct declaration name
    
    for chunk in sources:
        metadata = chunk.get("metadata", {})
        raw_source_path = metadata.get("source", "")
        
        if not raw_source_path:
            continue
            
        clean_filename = os.path.basename(raw_source_path)
        
        # 🟢 CRITICAL FIXED LINE: Spelling typo corrected from 'seen_soruces' to 'seen_sources'
        if clean_filename in seen_sources:
            continue
        seen_sources.add(clean_filename)
        
        formatted.append({
            "file_name": str(clean_filename),
            "download_url": f"/source/{clean_filename}",
            "file_type": metadata.get("file_type", "").lower(),
            "location": format_location(metadata),
            "snippet": chunk.get("text", "")[:200]
        })
        
    return formatted
