#!/usr/bin/env python3
"""Rebuild index.json by scanning all existing data files."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "public" / "data"
INDEX_JSON = DATA_DIR / "index.json"

def slugify(name: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]+", "-", name.lower())).strip("-")

def main():
    """Rebuild index.json by scanning existing data files."""
    if not DATA_DIR.exists():
        print("❌ Data directory not found")
        return
    
    index = []
    
    # Scan all prompt directories
    for prompt_dir in DATA_DIR.iterdir():
        if not prompt_dir.is_dir():
            continue
            
        prompt_slug = prompt_dir.name
        models = []
        
        # Scan all model JSON files in this prompt directory
        for model_file in prompt_dir.glob("*.json"):
            model_name = model_file.stem
            models.append({
                "name": model_name,
                "card": f"{prompt_slug}/{model_file.name}"
            })
        
        if models:
            # Create entry for this prompt
            entry = {
                "promptSlug": prompt_slug,
                "title": prompt_slug.replace("-", " "),
                "dateRun": datetime.now(timezone.utc).date().isoformat(),
                "models": sorted(models, key=lambda x: x["name"])
            }
            index.append(entry)
            print(f"✓ Found {len(models)} models for {prompt_slug}")
    
    # Sort by date (newest first)
    index.sort(key=lambda e: e["dateRun"], reverse=True)
    
    # Write the rebuilt index
    with open(INDEX_JSON, 'w') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Rebuilt index.json with {len(index)} prompts")
    total_models = sum(len(entry["models"]) for entry in index)
    print(f"✓ Total model combinations: {total_models}")

if __name__ == "__main__":
    main() 