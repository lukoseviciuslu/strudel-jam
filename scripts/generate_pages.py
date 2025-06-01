#!/usr/bin/env python3
"""Generate individual prompt pages from template."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_JSON = ROOT / "public" / "data" / "index.json"
PROMPTS_DIR = ROOT / "public" / "prompts"
TEMPLATE = ROOT / "public" / "p" / "template.html"
PAGES_DIR = ROOT / "public" / "p"

def slugify(name: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9-]+", "-", name.lower())).strip("-")

def discover_prompts():
    """Discover all prompts in the prompts directory."""
    prompts = {}
    for p in PROMPTS_DIR.iterdir():
        if p.is_file() and p.suffix in ['.md', '.txt']:
            slug = slugify(p.stem)
            prompts[slug] = {
                'slug': slug,
                'title': p.stem.replace('-', ' ').title(),
                'file': p.name
            }
    return prompts

def main():
    if not TEMPLATE.exists():
        print("Template not found at public/p/template.html")
        return
    
    template_content = TEMPLATE.read_text()
    
    # Discover all prompts
    all_prompts = discover_prompts()
    
    # Load existing index if it exists
    existing_index = []
    if INDEX_JSON.exists():
        existing_index = json.loads(INDEX_JSON.read_text())
    
    # Create a set of existing prompt slugs for reference
    indexed_slugs = {entry["promptSlug"] for entry in existing_index}
    
    generated_count = 0
    for slug, prompt_info in all_prompts.items():
        page_path = PAGES_DIR / f"{slug}.html"
        page_path.write_text(template_content)
        
        status = "✓" if slug in indexed_slugs else "○"
        print(f"{status} Generated: {page_path}")
        generated_count += 1
    
    print(f"\n✓ Generated {generated_count} prompt pages")
    print(f"✓ {len(indexed_slugs)} have benchmark data")
    print(f"○ {len(all_prompts) - len(indexed_slugs)} are new/pending")

if __name__ == "__main__":
    main() 