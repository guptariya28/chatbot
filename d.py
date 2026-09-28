for chunk in sources:
        metadata = chunk.get("metadata", {})
        raw_source_path = metadata.get("source", "")
        
        if not raw_source_path:
            continue
            
        # Extract strictly the final filename (e.g., 'Policy_2026.pdf' instead of 'C:/Users/.../Finance/Policy_2026.pdf')
        clean_filename = os.path.basename(raw_source_path)
        
        # Deduplicate the list to keep the UI clean and readable
        if clean_filename in seen_sources:
            continue
        seen_sources.add(clean_filename)
        
        formatted.append({
            "file_name": str(clean_filename),
            # This generates a secure relative URL link matching your /source/<path:filename> route
            "download_url": f"/source/{clean_filename}",
            "file_type": metadata.get("file_type", "").lower(),
            "location": format_location(metadata),
            "snippet": chunk.get("text", "")[:200]
        })
        
    return formatted
