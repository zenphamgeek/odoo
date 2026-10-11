#!/usr/bin/env python3
"""
Refactor and Un-Slop enterprise/innokafe_website/views/products.xml.
Replaces harsh border-warning and border-secondary cards with .inno-craft-card.
Embeds authentic curated Pexels photography headers into each product SKU card.
Purges box-in-box nesting and validates XML with xml.etree.ElementTree.
"""

import re
import xml.etree.ElementTree as ET

PRODUCTS_PATH = "enterprise/innokafe_website/views/products.xml"

SKU_PHOTOS = {
    "INNO-ROBUSTA-NAT-01": "/innokafe_website/static/src/img/photography/farm_cherries_ripe.webp",
    "INNO-ARABICA-WASH-02": "/innokafe_website/static/src/img/photography/farm_plantation_mist.webp",
    "INNO-SIGNATURE-HONEY-03": "/innokafe_website/static/src/img/photography/artisan_drying_sun.webp",
    "INNO-DRIP-EXPLORER-04": "/innokafe_website/static/src/img/photography/extraction_pourover_v60.webp",
    "INNO-COLDBREW-CITRUS-05": "/innokafe_website/static/src/img/photography/sensory_cupping_flight.webp",
    "INNO-HORECA-BARISTA-06": "/innokafe_website/static/src/img/photography/extraction_espresso_crema.webp",
}

def perform_products_unslop():
    with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Replace main product card containers
    old_card_cls = 'class="card h-100 bg-black bg-opacity-60 border border-secondary border-opacity-30 rounded-4 p-4 text-white d-flex flex-column justify-content-between inno-product-card"'
    new_card_cls = 'class="inno-craft-card h-100 rounded-4 p-4 text-white d-flex flex-column justify-content-between inno-product-card"'
    content = content.replace(old_card_cls, new_card_cls)

    # 2. Replace nested boxes with inno-inner-panel
    content = content.replace(
        'class="p-3 rounded-3 bg-black bg-opacity-40 border border-secondary border-opacity-20 mb-3 small"',
        'class="p-3 rounded-3 inno-inner-panel mb-3 small"'
    )
    content = content.replace(
        'class="p-4 rounded-4 bg-black bg-opacity-50 border border-secondary border-opacity-25 text-start"',
        'class="p-4 rounded-4 inno-craft-card text-start"'
    )
    content = content.replace(
        'class="card bg-black bg-opacity-60 border border-warning border-opacity-30 rounded-4 p-4 text-center text-white"',
        'class="inno-craft-card rounded-4 p-4 text-center text-white"'
    )
    content = content.replace(
        'class="p-3 rounded-3 bg-black bg-opacity-40 border border-secondary border-opacity-25"',
        'class="p-3 rounded-3 inno-inner-panel"'
    )

    # 3. Inject visual photography banner into each SKU card right before badges
    for sku, photo_path in SKU_PHOTOS.items():
        pattern = rf'(data-sku="{sku}"[^>]*>\s*<div>\s*)(<div class="d-flex justify-content-between align-items-center mb-3">)'
        match = re.search(pattern, content)
        if match:
            photo_banner = f"""<div class="position-relative rounded-3 overflow-hidden mb-3" style="aspect-ratio: 16 / 9;">
                                            <img src="{photo_path}" alt="{sku}" class="w-100 h-100 object-fit-cover"/>
                                            <div class="position-absolute top-0 start-0 w-100 h-100" style="background: linear-gradient(180deg, transparent 40%, rgba(20, 12, 7, 0.85) 100%);"/>
                                        </div>\n                                        """
            content = content[:match.start(2)] + photo_banner + content[match.start(2):]
            print(f"[✓] Injected photography banner for {sku}: {photo_path}")

    # 4. Validate with ElementTree
    try:
        ET.fromstring(content)
        print("[✓] products.xml parsed cleanly with ElementTree!")
    except ET.ParseError as err:
        print(f"[!] XML Validation Error in products.xml: {err}")
        return False

    with open(PRODUCTS_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✓] Successfully wrote un-slopped products catalogue to {PRODUCTS_PATH}")
    return True

if __name__ == "__main__":
    success = perform_products_unslop()
    if not success:
        exit(1)
