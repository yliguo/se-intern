import requests
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo  # Python 3.9+
 
# Config
SOURCE_README = (
    "https://raw.githubusercontent.com/jobright-ai/2026-Software-Engineer-Internship/master/README.md"
)
HISTORY_FILE = Path("data/history.json")
MAX_HISTORY = 24  # Keep last 24 batches (72 hours, 3 days)

def fetch_source():
    """Fetch raw README from Jobright repo."""
    r = requests.get(SOURCE_README, timeout=30)
    r.raise_for_status()
    return r.text

def extract_table(md):
    """Extract table rows from Jobright README"""
    lines = md.splitlines()
    table = []
    in_table = False
    for line in lines:
        if line.startswith("| Company"):
            in_table = True
            continue
        if in_table and line.startswith("|---"):
            continue
        if in_table:
            if not line.startswith("|"):
                break
            table.append(line.strip())
    return table

def load_history():
    """Load history from JSON; return empty list if missing."""
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    """Save updated history to JSON."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def build_readme(history):
    """Build README.md content from history, removing duplicates."""
    header = """# 💼 Finance & Accounting Internships (Live)

Automatically synced from **jobright-ai/2026-Software-Engineer-Internship**  
⏱ Updated every 3 hours via GitHub Actions

---
"""
    if not history:
        return header + "_No internships found in last 24 hours_\n"

    readme_md = header
    seen = set()  # Track unique rows across all batches

    for batch in history:
        timestamp = batch["timestamp"]
        rows = batch["rows"]

        # Remove duplicates
        unique_rows = []
        for row in rows:
            key = row  # Using the full row string as the unique key
            if key not in seen:
                seen.add(key)
                unique_rows.append(row)

        if not unique_rows:
            continue  # Skip batch if all rows were duplicates

        # Add timestamp heading
        readme_md += f"### 🕒 Batch updated: {timestamp}\n\n"

        # Add Markdown table
        readme_md += "| Company | Role | Location | Type | Date Posted | Link |\n"
        readme_md += "|--------|------|----------|------|-------------|------|\n"
        for row in unique_rows:
            readme_md += row + "\n"
        readme_md += "\n"

    return readme_md

def main():
    # Fetch latest data
    source = fetch_source()
    new_rows = extract_table(source)
    if not new_rows:
        print("No new rows found. Exiting.")
        return

    # Load previous history
    history = load_history()

    # Add new batch with timestamp at the top
    eastern = ZoneInfo("America/New_York")
    timestamp = datetime.now(tz=eastern).strftime("%Y-%m-%d %H:%M ET")
    history.insert(0, {"timestamp": timestamp, "rows": new_rows})

    # Keep only last MAX_HISTORY batches
    history = history[:MAX_HISTORY]

    # Save updated history
    save_history(history)

    # Build README.md
    readme = build_readme(history)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    print(f"Saved README with {len(new_rows)} new rows. Total batches: {len(history)}")

if __name__ == "__main__":
    main()
