#!/usr/bin/env python3
path = 'enterprise/insilos_website/static/src/js/innoria_topology_3d.js'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# Brand palette update
old_palette = """    const BRAND_PALETTE = {
        electricSapphire: 0x2F80ED, // Primary brand blue (#2F80ED)
        mintCyan: 0xB2FFDA,         // High-contrast mint cyan (#B2FFDA)
        techCyan: 0x0ABBDB,         // Vivid tech cyan (#0ABBDB)
        warmAmber: 0xFF9C00,        // Blockchain warm amber (#FF9C00)
        warmAmberAccent: 0xFE8B20,  // Deep amber (#FE8B20)
        darkBase: 0x05101E,         // Deep space dark base (#05101E)
        gridLines: 0x112740,        // Subtle coordinate grid (#112740)
        whiteHighContrast: 0xFFFFFF // High contrast white
    };"""

new_palette = """    const BRAND_PALETTE = {
        electricSapphire: 0x0284C7, // Corporate ocean blue (#0284C7)
        mintCyan: 0x0ABBDB,         // Innoria cyan (#0ABBDB)
        techCyan: 0x0ABBDB,         // Vivid tech cyan (#0ABBDB)
        warmAmber: 0xFF8000,        // Brand orange (#FF8000)
        warmAmberAccent: 0xEA580C,  // Deep orange (#EA580C)
        darkBase: 0xF0F9FF,         // Light ice blue base (#F0F9FF)
        gridLines: 0xBAE6FD,        // Soft blue grid lines (#BAE6FD)
        whiteHighContrast: 0x0F172A // Dark slate (#0F172A)
    };"""

text = text.replace(old_palette, new_palette)

# Fog and ambient light
text = text.replace(
    'this.scene.fog = new THREE.FogExp2(BRAND_PALETTE.darkBase, 0.035);',
    'this.scene.fog = new THREE.FogExp2(0xF0F9FF, 0.015);'
)
text = text.replace(
    'const ambient = new THREE.AmbientLight(0x0e1c31, 1.8);',
    'const ambient = new THREE.AmbientLight(0xFFFFFF, 2.2);'
)
text = text.replace(
    'grid.material.opacity = 0.22;',
    'grid.material.opacity = 0.55;'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)

print("enterprise/insilos_website/static/src/js/innoria_topology_3d.js updated for Light Theme!")
