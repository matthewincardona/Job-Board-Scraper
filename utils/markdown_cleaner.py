import re

def clean_markdown(text: str) -> str:
    if not text:
        return ""

    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Fix escaped characters
    text = (
        text
        .replace("\\-", "-")
        .replace("\\*", "*")
        .replace("\\+", "+")
        .replace("\\_", "_")
        .replace("\\#", "#")
    )

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    lines = text.split("\n")
    cleaned_lines = []
    prev_was_blank = False
    in_list = False

    for line in lines:
        stripped = line.lstrip()

        # Handle blank lines
        if stripped == "":
            if not prev_was_blank:
                cleaned_lines.append("")
                prev_was_blank = True
            in_list = False
            continue

        prev_was_blank = False

        # Normalize bullet characters
        if stripped.startswith("• "):
            stripped = "* " + stripped[2:]
        elif stripped.startswith(("◦ ", "▪ ", "▫ ", "▸ ", "▹ ")):
            stripped = "* " + stripped[2:]

        # Detect list items
        is_list_item = (
            stripped.startswith(("* ", "- ", "+ ")) or
            re.match(r'^\d+\.\s', stripped)
        )

        # Detect headers (markdown headers or bold text that looks like headers)
        is_header = (
            stripped.startswith("#") or
            (stripped.startswith("**") and stripped.endswith("**") and len(stripped.split()) <= 8)
        )

        # CRITICAL: Add blank line before list starts
        if is_list_item and not in_list:
            # Only add blank line if previous line wasn't already blank
            if cleaned_lines and cleaned_lines[-1] != "":
                cleaned_lines.append("")
            in_list = True
        
        # If we're exiting a list
        if not is_list_item and in_list:
            in_list = False

        # Add blank line after headers (so lists after headers work)
        if is_header and cleaned_lines:
            if cleaned_lines[-1] != "":
                cleaned_lines.append("")
        
        cleaned_lines.append(stripped)

        # Add blank line after headers for proper spacing
        if is_header:
            cleaned_lines.append("")

    # Join lines
    cleaned = "\n".join(cleaned_lines)

    # Normalize multiple blank lines to max 2
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Clean up extra spaces
    cleaned = re.sub(r' {3,}', ' ', cleaned)

    return cleaned.strip()