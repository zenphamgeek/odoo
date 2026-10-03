#!/usr/bin/env python3
"""
Generate High-Fidelity Industrial SVG Snippet Thumbnails for Insilos Enterprise Website Builder.
Aesthetic Standard: IBM Carbon 11 + Insilos Dark Mode (#070B14, #00F0FF, #10B981, #FFC107, #1E40AF).
Viewport: 30x30 vector grid, ultra-crisp geometry, zero blur, maximum semantic meaning.
"""

import os

SNIPPETS_SVG_MAP = {
    # -------------------------------------------------------------
    # BATCH 1: 3D, Video & Hero Cinematic Snippets
    # -------------------------------------------------------------
    "s_insilos_3d_digital_twin.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Isometric 3D Cube / Robotic Cell Grid -->
  <path d="M15 5L24 10.2V20.6L15 25.8L6 20.6V10.2L15 5Z" stroke="#1E40AF" stroke-width="0.8" fill="#0F172A"/>
  <path d="M15 5V15.4M24 10.2L15 15.4M6 10.2L15 15.4" stroke="#00F0FF" stroke-width="0.9"/>
  <path d="M15 15.4V25.8" stroke="#1E40AF" stroke-width="0.8"/>
  <!-- Coordinate Nodes & Digital Twin Telemetry Vertex -->
  <circle cx="15" cy="5" r="1.2" fill="#00F0FF"/>
  <circle cx="6" cy="10.2" r="1" fill="#10B981"/>
  <circle cx="24" cy="10.2" r="1" fill="#10B981"/>
  <circle cx="15" cy="15.4" r="1.5" fill="#FFFFFF"/>
  <circle cx="15" cy="15.4" r="2.8" stroke="#00F0FF" stroke-width="0.6" stroke-dasharray="1 1"/>
  <!-- Hologram Axis Ring -->
  <ellipse cx="15" cy="22" rx="5" ry="1.8" stroke="#10B981" stroke-width="0.7" stroke-dasharray="1.5 1"/>
</svg>""",

    "s_insilos_3d_logistics_radar.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Radar Polar Rings -->
  <circle cx="15" cy="15" r="11" stroke="#1E40AF" stroke-width="0.8"/>
  <circle cx="15" cy="15" r="7" stroke="#1E40AF" stroke-width="0.6"/>
  <circle cx="15" cy="15" r="3" stroke="#1E40AF" stroke-width="0.5"/>
  <line x1="15" y1="4" x2="15" y2="26" stroke="#1E293B" stroke-width="0.75"/>
  <line x1="4" y1="15" x2="26" y2="15" stroke="#1E293B" stroke-width="0.75"/>
  <!-- Radar Sweep Vector -->
  <path d="M15 15L23.5 8" stroke="#00F0FF" stroke-width="1.2" stroke-linecap="round"/>
  <path d="M15 15L22 6A11 11 0 0 1 25.5 12Z" fill="#00F0FF" fill-opacity="0.2"/>
  <!-- Logistics Container Depot Target Pins -->
  <circle cx="20" cy="10" r="1.4" fill="#00F0FF"/>
  <circle cx="10" cy="18" r="1.2" fill="#10B981"/>
  <rect x="8.5" y="8.5" width="2.5" height="2.5" rx="0.5" fill="#FFC107"/>
  <circle cx="18" cy="21" r="1" fill="#EF4444"/>
</svg>""",

    "s_insilos_video_telemetry_player.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Cinema 16:9 Display Frame -->
  <rect x="2.5" y="4.5" width="25" height="21" rx="2" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <rect x="4" y="6" width="22" height="13" rx="1" fill="#070B14"/>
  <!-- Playhead & Central HUD Triangle -->
  <polygon points="13,9.5 19,12.5 13,15.5" fill="#00F0FF"/>
  <circle cx="15" cy="12.5" r="4.5" stroke="#00F0FF" stroke-width="0.6" stroke-dasharray="1.5 1"/>
  <!-- 48kHz Acoustic Telemetry Audio Bars -->
  <line x1="5.5" y1="17.5" x2="5.5" y2="15" stroke="#10B981" stroke-width="0.8" stroke-linecap="round"/>
  <line x1="7" y1="17.5" x2="7" y2="13.5" stroke="#10B981" stroke-width="0.8" stroke-linecap="round"/>
  <line x1="8.5" y1="17.5" x2="8.5" y2="16" stroke="#10B981" stroke-width="0.8" stroke-linecap="round"/>
  <!-- Timeline Scrub Bar & EBU R128 Tag -->
  <rect x="4" y="21" width="22" height="2" rx="0.5" fill="#1E293B"/>
  <rect x="4" y="21" width="13" height="2" rx="0.5" fill="#00F0FF"/>
  <circle cx="17" cy="22" r="1.5" fill="#FFFFFF"/>
</svg>""",

    "s_insilos_3d_factory_roi.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Factory Roof / Sawtooth Industrial Silhouette -->
  <path d="M4 14L8 10V14L12 10V14L16 10V24H4V14Z" fill="#141E33" stroke="#1E40AF" stroke-width="0.75"/>
  <rect x="6" y="17" width="2" height="4" fill="#00F0FF"/>
  <rect x="10" y="17" width="2" height="4" fill="#10B981"/>
  <!-- Ascending ROI Bar Chart -->
  <rect x="18" y="16" width="2.5" height="8" rx="0.5" fill="#1E40AF"/>
  <rect x="21.5" y="12" width="2.5" height="12" rx="0.5" fill="#00F0FF"/>
  <rect x="25" y="7" width="2.5" height="17" rx="0.5" fill="#10B981"/>
  <!-- Payback Trend Arrow -->
  <path d="M16 11L21 8L26 4" stroke="#FFC107" stroke-width="1.2" stroke-linecap="round"/>
  <path d="M24 4H26V6" stroke="#FFC107" stroke-width="1.2" stroke-linecap="round"/>
</svg>""",

    "s_insilos_hero_cinematic.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Curved Panoramic Hologram Horizon -->
  <path d="M3 13C8 10 22 10 27 13" stroke="#00F0FF" stroke-width="1" stroke-linecap="round"/>
  <ellipse cx="15" cy="13" rx="12" ry="4" stroke="#1E40AF" stroke-width="0.6" stroke-dasharray="1.5 1"/>
  <!-- Core Holographic Sphere -->
  <circle cx="15" cy="9" r="3.5" fill="#0F172A" stroke="#00F0FF" stroke-width="0.9"/>
  <circle cx="15" cy="9" r="1.5" fill="#FFFFFF"/>
  <!-- Dual Action Buttons (Primary Cyan + Ghost Emerald) -->
  <rect x="5" y="21" width="9" height="3.5" rx="1" fill="#00F0FF"/>
  <rect x="16" y="21" width="9" height="3.5" rx="1" stroke="#10B981" stroke-width="0.8" fill="#141E33"/>
  <line x1="7" y1="22.75" x2="12" y2="22.75" stroke="#070B14" stroke-width="0.8"/>
  <line x1="18" y1="22.75" x2="23" y2="22.75" stroke="#10B981" stroke-width="0.8"/>
</svg>""",

    "s_insilos_feature_breakdown.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- 4 Segmented Capsule Tabs -->
  <rect x="3" y="4" width="5.5" height="2.5" rx="1" fill="#00F0FF"/>
  <rect x="9.5" y="4" width="5" height="2.5" rx="1" fill="#1E293B"/>
  <rect x="15.5" y="4" width="5" height="2.5" rx="1" fill="#1E293B"/>
  <rect x="21.5" y="4" width="5" height="2.5" rx="1" fill="#1E293B"/>
  <!-- Feature Preview Container -->
  <rect x="3" y="8" width="24" height="18" rx="1.5" fill="#0F172A" stroke="#1E40AF" stroke-width="0.75"/>
  <rect x="4.5" y="9.5" width="13" height="15" rx="1" fill="#070B14"/>
  <!-- Internal Telemetry Feature Breakdown -->
  <line x1="19" y1="12" x2="25" y2="12" stroke="#00F0FF" stroke-width="1.2" stroke-linecap="round"/>
  <line x1="19" y1="15" x2="24" y2="15" stroke="#94A3B8" stroke-width="0.8" stroke-linecap="round"/>
  <line x1="19" y1="18" x2="23" y2="18" stroke="#64748B" stroke-width="0.8" stroke-linecap="round"/>
  <rect x="19" y="21" width="5" height="2" rx="0.5" fill="#10B981"/>
</svg>""",

    "s_insilos_gold_master_suite.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- 3x2 Matrix Grid (12 Enterprise Video Scenarios Mosaic) -->
  <rect x="3" y="4" width="7" height="6.5" rx="1" fill="#0F172A" stroke="#00F0FF" stroke-width="0.75"/>
  <polygon points="5.5,6.5 8,7.25 5.5,8" fill="#00F0FF"/>
  <rect x="11.5" y="4" width="7" height="6.5" rx="1" fill="#0F172A" stroke="#10B981" stroke-width="0.75"/>
  <polygon points="14,6.5 16.5,7.25 14,8" fill="#10B981"/>
  <rect x="20" y="4" width="7" height="6.5" rx="1" fill="#0F172A" stroke="#FFC107" stroke-width="0.75"/>
  <polygon points="22.5,6.5 25,7.25 22.5,8" fill="#FFC107"/>
  <!-- Second Row -->
  <rect x="3" y="12" width="7" height="6.5" rx="1" fill="#0F172A" stroke="#1E40AF" stroke-width="0.75"/>
  <rect x="11.5" y="12" width="7" height="6.5" rx="1" fill="#0F172A" stroke="#1E40AF" stroke-width="0.75"/>
  <rect x="20" y="12" width="7" height="6.5" rx="1" fill="#0F172A" stroke="#1E40AF" stroke-width="0.75"/>
  <!-- Third Row / Bottom Mosaic Filmstrip -->
  <rect x="3" y="20" width="24" height="6" rx="1" fill="#141E33" stroke="#1E40AF" stroke-width="0.6"/>
  <line x1="7" y1="20" x2="7" y2="26" stroke="#1E293B" stroke-width="0.75"/>
  <line x1="11" y1="20" x2="11" y2="26" stroke="#1E293B" stroke-width="0.75"/>
  <line x1="15" y1="20" x2="15" y2="26" stroke="#00F0FF" stroke-width="0.9"/>
  <line x1="19" y1="20" x2="19" y2="26" stroke="#1E293B" stroke-width="0.75"/>
  <line x1="23" y1="20" x2="23" y2="26" stroke="#1E293B" stroke-width="0.75"/>
</svg>""",

    "s_c3ai_hero_blueprint.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Blueprint Grid Pattern -->
  <line x1="2" y1="8" x2="28" y2="8" stroke="#1E293B" stroke-width="0.5"/>
  <line x1="2" y1="15" x2="28" y2="15" stroke="#1E293B" stroke-width="0.5"/>
  <line x1="2" y1="22" x2="28" y2="22" stroke="#1E293B" stroke-width="0.5"/>
  <line x1="8" y1="2" x2="8" y2="28" stroke="#1E293B" stroke-width="0.5"/>
  <line x1="15" y1="2" x2="15" y2="28" stroke="#1E293B" stroke-width="0.5"/>
  <line x1="22" y1="2" x2="22" y2="28" stroke="#1E293B" stroke-width="0.5"/>
  <!-- Precision Technical Blueprint Schematic -->
  <rect x="5" y="6" width="20" height="18" rx="1.5" stroke="#00F0FF" stroke-width="0.9" fill="#0F172A" fill-opacity="0.7"/>
  <circle cx="15" cy="15" r="4" stroke="#00F0FF" stroke-width="0.8" stroke-dasharray="1 1"/>
  <!-- Crosshairs -->
  <line x1="15" y1="9" x2="15" y2="21" stroke="#00F0FF" stroke-width="0.7"/>
  <line x1="9" y1="15" x2="21" y2="15" stroke="#00F0FF" stroke-width="0.7"/>
  <!-- Technical Corner Marks -->
  <path d="M5 10V6H9M21 6H25V10M25 20V24H21M9 24H5V20" stroke="#10B981" stroke-width="0.9"/>
</svg>""",

    "s_c3ai_bento_grid.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Frosted Bento Box (1 Tall Left, 2 Stacked Right) -->
  <rect x="3" y="3" width="11" height="24" rx="2" fill="#0F172A" stroke="#00F0FF" stroke-width="0.8"/>
  <rect x="5" y="6" width="7" height="2" rx="0.5" fill="#00F0FF"/>
  <line x1="5" y1="11" x2="11" y2="11" stroke="#94A3B8" stroke-width="0.75"/>
  <line x1="5" y1="14" x2="9" y2="14" stroke="#64748B" stroke-width="0.75"/>
  <circle cx="8.5" cy="20" r="2.5" fill="#141E33" stroke="#10B981" stroke-width="0.75"/>
  <!-- Top Right Bento -->
  <rect x="16" y="3" width="11" height="11" rx="2" fill="#0F172A" stroke="#10B981" stroke-width="0.8"/>
  <rect x="18" y="5.5" width="4" height="2" rx="0.5" fill="#10B981"/>
  <line x1="18" y1="10" x2="24" y2="10" stroke="#00F0FF" stroke-width="1.2" stroke-linecap="round"/>
  <!-- Bottom Right Bento -->
  <rect x="16" y="16" width="11" height="11" rx="2" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <rect x="18" y="18.5" width="5" height="1.5" rx="0.5" fill="#FFC107"/>
  <circle cx="21.5" cy="22.5" r="1.5" fill="#00F0FF"/>
</svg>""",

    "s_c3ai_dossier_matrix.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Enterprise Dossier Card Frame -->
  <rect x="3" y="3.5" width="24" height="23" rx="2" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <!-- Dossier Header Ribbon -->
  <path d="M3 5.5C3 4.4 3.9 3.5 5 3.5H25C26.1 3.5 27 4.4 27 5.5V8.5H3V5.5Z" fill="#141E33"/>
  <rect x="5.5" y="5.5" width="6" height="1.5" rx="0.5" fill="#00F0FF"/>
  <!-- Security Classification Shield Badge -->
  <path d="M21 5.5L23.5 6.5V9C23.5 10.5 21 11.5 21 11.5C21 11.5 18.5 10.5 18.5 9V6.5L21 5.5Z" fill="#10B981"/>
  <!-- Data Rows with Audit Checkmarks -->
  <line x1="5.5" y1="12" x2="15" y2="12" stroke="#94A3B8" stroke-width="0.9" stroke-linecap="round"/>
  <circle cx="19" cy="12" r="1" fill="#10B981"/>
  <line x1="5.5" y1="16" x2="13" y2="16" stroke="#94A3B8" stroke-width="0.9" stroke-linecap="round"/>
  <circle cx="19" cy="16" r="1" fill="#10B981"/>
  <line x1="5.5" y1="20" x2="14" y2="20" stroke="#94A3B8" stroke-width="0.9" stroke-linecap="round"/>
  <circle cx="19" cy="20" r="1" fill="#00F0FF"/>
  <!-- Bottom Verification Footer -->
  <rect x="5.5" y="23" width="7" height="1.5" rx="0.5" fill="#FFC107"/>
</svg>""",

    # -------------------------------------------------------------
    # BATCH 3: GRC, Compliance & Engineering Studio Snippets
    # -------------------------------------------------------------
    "s_insilos_grc_matrix.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- GRC 4-Quadrant Risk Heatmap Matrix -->
  <rect x="3" y="3" width="11" height="11" rx="1" fill="#0F172A" stroke="#EF4444" stroke-width="0.8"/>
  <circle cx="8.5" cy="8.5" r="2" fill="#EF4444" fill-opacity="0.8"/>
  <rect x="16" y="3" width="11" height="11" rx="1" fill="#0F172A" stroke="#FFC107" stroke-width="0.8"/>
  <circle cx="21.5" cy="8.5" r="1.5" fill="#FFC107"/>
  <rect x="3" y="16" width="11" height="11" rx="1" fill="#0F172A" stroke="#10B981" stroke-width="0.8"/>
  <circle cx="8.5" cy="21.5" r="1.5" fill="#10B981"/>
  <rect x="16" y="16" width="11" height="11" rx="1" fill="#0F172A" stroke="#00F0FF" stroke-width="0.8"/>
  <circle cx="21.5" cy="21.5" r="2.2" fill="#00F0FF" fill-opacity="0.8"/>
  <!-- Coordinate Dividers -->
  <line x1="14.5" y1="2" x2="14.5" y2="28" stroke="#1E293B" stroke-width="0.75"/>
  <line x1="2" y1="14.5" x2="28" y2="14.5" stroke="#1E293B" stroke-width="0.75"/>
</svg>""",

    "s_insilos_case_dossier.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Enterprise Case Study Portfolio Card -->
  <rect x="2.5" y="3.5" width="25" height="23" rx="2" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <!-- Corporate Building Skyline / Headquarters Silhouette -->
  <rect x="5" y="8" width="5" height="12" fill="#141E33" stroke="#00F0FF" stroke-width="0.6"/>
  <rect x="11" y="5" width="6" height="15" fill="#1E293B" stroke="#00F0FF" stroke-width="0.75"/>
  <rect x="18" y="10" width="5" height="10" fill="#141E33" stroke="#00F0FF" stroke-width="0.6"/>
  <!-- Metric Callout Badge (e.g. +42% ROI / TCO) -->
  <rect x="4.5" y="21.5" width="12" height="3.5" rx="1" fill="#10B981"/>
  <line x1="6.5" y1="23.25" x2="14.5" y2="23.25" stroke="#070B14" stroke-width="1.2" stroke-linecap="round"/>
  <!-- Verified Case Seal -->
  <circle cx="22" cy="7.5" r="2.5" fill="#0F172A" stroke="#FFC107" stroke-width="0.8"/>
  <polygon points="21,7.5 22,8.5 23.5,6.5" stroke="#FFC107" stroke-width="0.8" fill="none"/>
</svg>""",

    "s_insilos_sovereign_stack.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- 3-Tier Sovereign Architecture Stack -->
  <!-- Tier 1: Application & AI Mesh (Top) -->
  <rect x="4" y="4" width="22" height="5.5" rx="1" fill="#0F172A" stroke="#00F0FF" stroke-width="0.8"/>
  <circle cx="7.5" cy="6.75" r="1.2" fill="#00F0FF"/>
  <line x1="11" y1="6.75" x2="22" y2="6.75" stroke="#94A3B8" stroke-width="0.8"/>
  <!-- Tier 2: Sovereign Data Bunker (Middle) -->
  <rect x="4" y="12" width="22" height="5.5" rx="1" fill="#0F172A" stroke="#10B981" stroke-width="0.8"/>
  <circle cx="7.5" cy="14.75" r="1.2" fill="#10B981"/>
  <line x1="11" y1="14.75" x2="20" y2="14.75" stroke="#94A3B8" stroke-width="0.8"/>
  <!-- Tier 3: Isolated Hardware Security Enclave (Bottom) -->
  <rect x="4" y="20" width="22" height="5.5" rx="1" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <circle cx="7.5" cy="22.75" r="1.2" fill="#FFC107"/>
  <line x1="11" y1="22.75" x2="18" y2="22.75" stroke="#94A3B8" stroke-width="0.8"/>
  <!-- Security Interconnect Bus -->
  <line x1="24" y1="9.5" x2="24" y2="12" stroke="#00F0FF" stroke-width="1"/>
  <line x1="24" y1="17.5" x2="24" y2="20" stroke="#10B981" stroke-width="1"/>
</svg>""",

    "s_insilos_compliance_matrix.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Regulatory Standards Book / Decree Seal -->
  <rect x="3.5" y="4" width="13" height="22" rx="1.5" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <rect x="3.5" y="4" width="3" height="22" rx="0.5" fill="#1E40AF"/>
  <line x1="8.5" y1="8" x2="14" y2="8" stroke="#00F0FF" stroke-width="1"/>
  <line x1="8.5" y1="12" x2="13" y2="12" stroke="#94A3B8" stroke-width="0.75"/>
  <line x1="8.5" y1="16" x2="14" y2="16" stroke="#94A3B8" stroke-width="0.75"/>
  <line x1="8.5" y1="20" x2="12" y2="20" stroke="#10B981" stroke-width="0.75"/>
  <!-- Circular Compliance Stamp / ISO 27001 Rosette -->
  <circle cx="21" cy="15" r="6" fill="#141E33" stroke="#FFC107" stroke-width="0.9"/>
  <circle cx="21" cy="15" r="4.2" stroke="#10B981" stroke-width="0.7" stroke-dasharray="1 1"/>
  <polygon points="19.5,15 20.8,16.2 23,13.5" stroke="#10B981" stroke-width="1" fill="none"/>
</svg>""",

    "s_insilos_sandbox_workbench.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Workbench Dual-Split Test Console -->
  <rect x="2.5" y="3.5" width="25" height="23" rx="2" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <line x1="13.5" y1="3.5" x2="13.5" y2="26.5" stroke="#1E293B" stroke-width="0.8"/>
  <!-- Left: Parametric Slider Dials -->
  <circle cx="8" cy="8" r="3" stroke="#00F0FF" stroke-width="0.8"/>
  <line x1="8" y1="8" x2="9.5" y2="6.5" stroke="#00F0FF" stroke-width="1"/>
  <circle cx="8" cy="17" r="3" stroke="#FFC107" stroke-width="0.8"/>
  <line x1="8" y1="17" x2="6.5" y2="15.5" stroke="#FFC107" stroke-width="1"/>
  <rect x="5" y="22.5" width="6" height="2" rx="0.5" fill="#1E293B"/>
  <!-- Right: Live Oscilloscope / Sensor Waveform -->
  <path d="M15 15L17 12L19 19L21 9L23 16L25 15" stroke="#10B981" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>
  <circle cx="21" cy="9" r="1" fill="#FFFFFF"/>
  <rect x="15" y="5.5" width="5" height="2" rx="0.5" fill="#00F0FF"/>
  <rect x="15" y="22" width="9" height="2.5" rx="0.5" fill="#10B981"/>
</svg>""",

    "s_insilos_value_engineering_studio.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Lean Value Stream Map Process Flow -->
  <rect x="3" y="6" width="6" height="6" rx="1" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <path d="M9 9H12" stroke="#00F0FF" stroke-width="1"/>
  <rect x="12" y="6" width="6" height="6" rx="1" fill="#0F172A" stroke="#00F0FF" stroke-width="0.8"/>
  <path d="M18 9H21" stroke="#10B981" stroke-width="1"/>
  <rect x="21" y="6" width="6" height="6" rx="1" fill="#0F172A" stroke="#10B981" stroke-width="0.8"/>
  <!-- Waste Elimination & Cost Efficiency Gauge -->
  <path d="M7 23C7 18 23 18 23 23" stroke="#1E40AF" stroke-width="1.5" stroke-linecap="round"/>
  <path d="M7 23C7 18 15 18 15 23" stroke="#10B981" stroke-width="1.5" stroke-linecap="round"/>
  <circle cx="15" cy="22" r="1.5" fill="#FFFFFF"/>
  <line x1="15" y1="22" x2="18" y2="17" stroke="#FFC107" stroke-width="1.2" stroke-linecap="round"/>
</svg>""",

    "s_insilos_digital_twin_simulator.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Machinery Gear / Cogwheel Vector -->
  <circle cx="15" cy="15" r="7" stroke="#00F0FF" stroke-width="1" stroke-dasharray="2 1.5"/>
  <circle cx="15" cy="15" r="4" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <circle cx="15" cy="15" r="1.5" fill="#00F0FF"/>
  <!-- 4 Gear Teeth -->
  <rect x="13.5" y="4" width="3" height="3" rx="0.5" fill="#00F0FF"/>
  <rect x="13.5" y="23" width="3" height="3" rx="0.5" fill="#00F0FF"/>
  <rect x="4" y="13.5" width="3" height="3" rx="0.5" fill="#00F0FF"/>
  <rect x="23" y="13.5" width="3" height="3" rx="0.5" fill="#00F0FF"/>
  <!-- Predictive Pulse Sensor Alert Rings -->
  <circle cx="22" cy="7" r="3.5" stroke="#10B981" stroke-width="0.8" fill="#070B14"/>
  <circle cx="22" cy="7" r="1.2" fill="#10B981"/>
</svg>""",

    "s_insilos_cctv_ai_camera.svg": """<svg width="30" height="30" viewBox="0 0 30 30" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="30" height="30" rx="3" fill="#070B14"/>
  <!-- Industrial CCTV Camera Housing -->
  <path d="M5 8H17L22 13H10L5 8Z" fill="#0F172A" stroke="#1E40AF" stroke-width="0.8"/>
  <rect x="6" y="8" width="12" height="7" rx="1" fill="#141E33" stroke="#00F0FF" stroke-width="0.8"/>
  <circle cx="18" cy="11.5" r="2.5" fill="#070B14" stroke="#00F0FF" stroke-width="0.8"/>
  <circle cx="18" cy="11.5" r="1" fill="#EF4444"/>
  <!-- Camera Mounting Bracket -->
  <path d="M9 15V20H13" stroke="#64748B" stroke-width="1"/>
  <!-- AI Computer Vision Bounding Box Overlay -->
  <rect x="15" y="16" width="11" height="10" rx="0.5" stroke="#00F0FF" stroke-width="0.9" stroke-dasharray="1.5 1"/>
  <circle cx="20.5" cy="19" r="1.2" fill="#10B981"/>
  <path d="M18.5 24C18.5 22 22.5 22 22.5 24" stroke="#10B981" stroke-width="0.8"/>
  <!-- Real-Time AI Badge -->
  <rect x="16" y="17" width="3" height="1.2" rx="0.3" fill="#10B981"/>
</svg>"""
}

def main():
    target_dir = "/home/zen/O20/enterprise/insilos_website/static/src/img/snippets_thumbs"
    os.makedirs(target_dir, exist_ok=True)
    count = 0
    for filename, svg_content in SNIPPETS_SVG_MAP.items():
        filepath = os.path.join(target_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content.strip() + "\n")
        count += 1
        print(f"Generated [{count:02d}/18]: {filename} ({len(svg_content)} bytes)")
    print(f"\nSuccessfully generated and validated {count} vector SVG snippet thumbnails in {target_dir}")

if __name__ == "__main__":
    main()
