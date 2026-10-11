#!/usr/bin/env python3
"""
Refactor and Un-Slop enterprise/innokafe_website/views/story.xml and solutions_b2b.xml.
Removes harsh card borders, box-in-box nesting, and AI slop.
Validates XML integrity with xml.etree.ElementTree.
"""

import xml.etree.ElementTree as ET

STORY_PATH = "enterprise/innokafe_website/views/story.xml"
B2B_PATH = "enterprise/innokafe_website/views/solutions_b2b.xml"

def unslop_story():
    with open(STORY_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace 4-No Pledge cards in story.xml
    content = content.replace(
        'class="card h-100 bg-black bg-opacity-50 border border-warning border-opacity-30 rounded-4 p-4 text-white"',
        'class="inno-craft-card h-100 rounded-4 p-4 text-white"'
    )
    content = content.replace(
        'class="card bg-black bg-opacity-50 border border-secondary border-opacity-25 rounded-4 p-4 text-white shadow-lg"',
        'class="inno-craft-card rounded-4 p-4 text-white shadow-lg"'
    )
    content = content.replace(
        'class="card bg-black bg-opacity-60 border border-secondary border-opacity-25 rounded-4 p-4 text-white"',
        'class="inno-craft-card rounded-4 p-4 text-white"'
    )
    content = content.replace(
        'class="card h-100 bg-black bg-opacity-50 border border-secondary border-opacity-25 rounded-4 p-4 text-white d-flex flex-column justify-content-between"',
        'class="inno-craft-card h-100 rounded-4 p-4 text-white d-flex flex-column justify-content-between"'
    )
    content = content.replace(
        'class="p-3 rounded-3 bg-black bg-opacity-50 border border-secondary border-opacity-15 mb-3"',
        'class="p-3 rounded-3 inno-inner-panel mb-3"'
    )
    content = content.replace(
        'class="p-3 rounded-3 bg-black bg-opacity-40 border border-secondary border-opacity-25"',
        'class="p-3 rounded-3 inno-inner-panel"'
    )
    content = content.replace(
        'class="p-3 rounded-3 bg-black bg-opacity-50 border border-secondary border-opacity-25 text-center flex-fill"',
        'class="p-3 rounded-3 inno-inner-panel text-center flex-fill"'
    )
    content = content.replace(
        'class="p-3 rounded-3 border border-warning border-opacity-25 mb-4 col-lg-11"',
        'class="p-3 rounded-3 inno-inner-panel mb-4 col-lg-11"'
    )

    try:
        ET.fromstring(content)
        print("[✓] story.xml parsed cleanly with ElementTree!")
    except ET.ParseError as err:
        print(f"[!] XML Validation Error in story.xml: {err}")
        return False

    with open(STORY_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✓] Successfully wrote un-slopped story to {STORY_PATH}")
    return True

def unslop_b2b():
    with open(B2B_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace dark cards with inno-craft-card
    content = content.replace(
        'class="card h-100 rounded-4 overflow-hidden border p-4 text-start d-flex flex-column justify-content-between"',
        'class="inno-craft-card h-100 rounded-4 overflow-hidden p-4 text-start d-flex flex-column justify-content-between"'
    )
    content = content.replace(
        'class="card h-100 rounded-4 border p-4 text-start d-flex flex-column justify-content-between"',
        'class="inno-craft-card h-100 rounded-4 p-4 text-start d-flex flex-column justify-content-between"'
    )
    content = content.replace(
        'class="card h-100 p-4 rounded-4 border" style="background-color: #2C1810; border-color: rgba(212, 136, 66, 0.25);"',
        'class="inno-craft-card h-100 p-4 rounded-4"'
    )
    content = content.replace(
        'class="card h-100 p-4 rounded-4 border d-flex flex-column justify-content-between"',
        'class="inno-craft-card h-100 p-4 rounded-4 d-flex flex-column justify-content-between"'
    )
    content = content.replace(
        'class="card rounded-4 p-4 p-lg-5 border"',
        'class="inno-craft-card rounded-4 p-4 p-lg-5"'
    )

    try:
        ET.fromstring(content)
        print("[✓] solutions_b2b.xml parsed cleanly with ElementTree!")
    except ET.ParseError as err:
        print(f"[!] XML Validation Error in solutions_b2b.xml: {err}")
        return False

    with open(B2B_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✓] Successfully wrote un-slopped b2b solutions to {B2B_PATH}")
    return True

if __name__ == "__main__":
    s1 = unslop_story()
    s2 = unslop_b2b()
    if not (s1 and s2):
        exit(1)
