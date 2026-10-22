#!/usr/bin/env python3
"""
tools/purge_all_robotic_slashes.py
Purges robotic '//' sci-fi slashes from all QWeb XML view files.
Converts them to clean, human-written enterprise typography:
- Leading '// ' -> ''
- Infix ' // ' -> ' · '
- Preserves xpath expressions (//snippets, //div, etc.)
- Preserves URLs (http://, https://, ipfs://)
- Preserves code syntax/token comments.
"""

from pathlib import Path
import re
import xml.etree.ElementTree as ET

VIEWS_DIR = Path("enterprise/insilos_website/views")

def unslop_file(p: Path):
    txt = p.read_text(encoding="utf-8")
    original = txt
    lines = txt.splitlines()
    new_lines = []

    for line in lines:
        # Skip xpath expressions, comments, or scripts
        if "<xpath" in line or "expr=\"//" in line or "expr='//" in line:
            new_lines.append(line)
            continue
        if "token-comment" in line or "token-string" in line:
            new_lines.append(line)
            continue
        if "http://" in line or "https://" in line or "ipfs://" in line:
            # Handle lines with URLs carefully: only replace // if not part of URL
            parts = re.split(r"(https?://\S+|ipfs://\S+)", line)
            cleaned_parts = []
            for part in parts:
                if part.startswith("http://") or part.startswith("https://") or part.startswith("ipfs://"):
                    cleaned_parts.append(part)
                else:
                    # Clean //
                    part = re.sub(r">(\s*)//\s*", r">\1", part)
                    part = re.sub(r"\s+//\s+", " · ", part)
                    cleaned_parts.append(part)
            new_lines.append("".join(cleaned_parts))
            continue

        # Normal line processing:
        # 1. Leading // right after tag: >// FOO -> >FOO, > // FOO -> > FOO
        line = re.sub(r">(\s*)//\s*", r">\1", line)
        # 2. Infix // with spaces: FOO // BAR -> FOO · BAR
        line = re.sub(r"\s+//\s+", " · ", line)
        # 3. Infix // without leading space: FOO// BAR -> FOO · BAR
        line = re.sub(r"([A-Za-z0-9_])//\s*", r"\1 · ", line)
        new_lines.append(line)

    result = "\n".join(new_lines) + "\n"
    if result != original:
        p.write_text(result, encoding="utf-8")
        # Validate XML
        try:
            ET.parse(p)
            print(f"  [OK] Cleaned {p.name}")
        except Exception as e:
            print(f"  [ERROR] XML Parse Error in {p.name}: {e}")
            p.write_text(original, encoding="utf-8")
            print(f"  [REVERTED] {p.name}")

def main():
    print("=" * 70)
    print("PURGING ROBOTIC // SLASH BADGES ACROSS ALL QWEB VIEWS")
    print("=" * 70)
    for p in sorted(VIEWS_DIR.glob("*.xml")):
        unslop_file(p)
    print("=" * 70)
    print("VALIDATING ALL VIEWS...")
    all_ok = True
    for p in sorted(VIEWS_DIR.glob("*.xml")):
        try:
            ET.parse(p)
        except Exception as e:
            print(f"  Invalid XML: {p.name}: {e}")
            all_ok = False
    if all_ok:
        print("  All XML views are 100% valid XML!")

if __name__ == "__main__":
    main()
