if not raw_sources and "[EXCEL_FAQ_DIRECT_HIT]" in last_ai_message:
            try:
                # Extract the raw serialized JSON tracking blocks hidden inside the message string
                json_str = last_ai_message.split("[EXCEL_FAQ_DIRECT_HIT]")[-1].strip()
                direct_hit_data = json.loads(json_str)
                if isinstance(direct_hit_data, dict):
                    raw_sources = [direct_hit_data]
                elif isinstance(direct_hit_data, list):
                    raw_sources = direct_hit_data
            except Exception:
                logger.warning("Failed to automatically unwrap hidden short-circuit source payloads.")

    except Exception as e:
        logger.error("Graph execution failure exception: %s", str(e), exc_info=True)
        return jsonify({"error": "Internal graph execution processing failed."}), 500
        
    # Compile the final raw sources array using the exact format alignment function
    compiled_sources_chips = _format_sources(raw_sources)
    
    # Clean up the display string answer message to shield technical JSON arrays from user view
    clean_display_answer = last_ai_message
    if "[EXCEL_FAQ_DIRECT_HIT]" in clean_display_answer:
        clean_display_answer = clean_display_answer.split("[EXCEL_FAQ_DIRECT_HIT]")[0].strip()
