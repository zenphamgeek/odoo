import os

scss_path = '/home/zen/O20/enterprise/insilos_website/static/src/scss/innoria_theme.scss'

with open(scss_path, 'r', encoding='utf-8') as f:
    content = f.read()

split_marker = '/* ==========================================================================\n   INNORIA 3D INTERACTIVE ARCHITECTURE DECK STYLES'
if split_marker not in content:
    split_marker = '/* =========================================================================='

idx = content.find('INNORIA 3D INTERACTIVE ARCHITECTURE DECK STYLES')
if idx == -1:
    raise ValueError("Marker not found in innoria_theme.scss")

# find the comment start before this
comment_start = content.rfind('/*', 0, idx)
base_content = content[:comment_start]

new_scss = '''/* ==========================================================================
   INNORIA 3D INTERACTIVE ARCHITECTURE DECK STYLES (DARK CYBER LUXURY)
   Hardware-Accelerated CSS 3D Isometric Engine // Pure Vector Typography
   ========================================================================== */
.s_innoria_3d_architecture_deck {
    background: #070B14 !important;
    color: #F8FAFC;

    .deck-app-container {
        width: 100%;
        max-width: 1320px;
        background: rgba(11, 19, 36, 0.95);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 28px;
        box-shadow: 0 24px 64px rgba(0, 0, 0, 0.7), 0 0 1px 1px rgba(255, 255, 255, 0.05);
        padding: 36px 40px;
        position: relative;
        overflow: hidden;
        margin: 0 auto;

        &::before {
            content: "";
            position: absolute;
            top: -120px;
            left: 10%;
            width: 550px;
            height: 550px;
            background: radial-gradient(circle, rgba(10, 187, 219, 0.12) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }
    }

    .header-bar {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 28px;
        position: relative;
        z-index: 2;
    }

    .brand-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 9999px;
        background: rgba(10, 187, 219, 0.12);
        color: #0ABBDB;
        border: 1px solid rgba(10, 187, 219, 0.35);
        margin-bottom: 8px;
    }

    .main-title {
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .main-title span.accent {
        background: linear-gradient(135deg, #0ABBDB, #00F0FF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .sub-title {
        font-size: 14px;
        color: #94A3B8 !important;
        margin-top: 4px;
    }

    .action-controls {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .btn-action {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 600;
        border-radius: 10px;
        cursor: pointer;
        border: 1px solid rgba(255, 255, 255, 0.12);
        background: rgba(15, 23, 42, 0.8);
        color: #E2E8F0;
        transition: all 0.2s ease;
        user-select: none;

        &:hover {
            background: rgba(10, 187, 219, 0.15);
            border-color: #0ABBDB;
            color: #00F0FF;
            transform: translateY(-1px);
        }

        &.active {
            background: #0ABBDB;
            color: #070B14;
            border-color: #0ABBDB;
            font-weight: 700;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #10B981;
            box-shadow: 0 0 8px #10B981;
        }
    }

    .deck-grid {
        display: grid;
        grid-template-columns: 500px 1fr;
        gap: 36px;
        align-items: stretch;
        position: relative;
        z-index: 2;

        @media (max-width: 1024px) {
            grid-template-columns: 1fr;
        }
    }

    .stage-card {
        background: radial-gradient(circle at 50% 50%, #0F1E36 0%, #070D18 100%);
        border: 1px solid rgba(10, 187, 219, 0.28);
        border-radius: 24px;
        box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), inset 0 0 30px rgba(10, 187, 219, 0.05);
        position: relative;
        min-height: 520px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        user-select: none;

        &::before {
            content: "";
            position: absolute;
            inset: 0;
            background-size: 24px 24px;
            background-image: 
                linear-gradient(to right, rgba(10, 187, 219, 0.08) 1px, transparent 1px),
                linear-gradient(to bottom, rgba(10, 187, 219, 0.08) 1px, transparent 1px);
            pointer-events: none;
        }
    }

    .scene-viewport {
        width: 400px;
        height: 420px;
        display: flex;
        align-items: center;
        justify-content: center;
        perspective: 1200px;
        perspective-origin: 50% 36%;
    }

    .deck-container-3d {
        width: 230px;
        height: 230px;
        position: relative;
        transform-style: preserve-3d;
        transition: transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    }

    .isometric-angle {
        transform: rotateX(58deg) rotateZ(-38deg) translateY(-15px);
    }

    .slab-layer {
        position: absolute;
        width: 230px;
        height: 230px;
        transform-style: preserve-3d;
        cursor: pointer;
        transition: transform 0.45s cubic-bezier(0.34, 1.4, 0.64, 1),
                    filter 0.35s ease,
                    opacity 0.35s ease;
    }

    #slab-0 { transform: translateZ(90px); }
    #slab-1 { transform: translateZ(30px); }
    #slab-2 { transform: translateZ(-30px); }
    #slab-3 { transform: translateZ(-90px); }

    .slab-layer.pulled-out {
        transform: translate3d(75px, 70px, 55px) scale3d(1.04, 1.04, 1.04) !important;
        z-index: 60 !important;
    }

    .slab-layer.dimmed {
        opacity: 0.3;
        filter: grayscale(60%) contrast(0.8);
    }

    .deck-exploded #slab-0 { transform: translateZ(155px) !important; }
    .deck-exploded #slab-1 { transform: translateZ(55px) !important; }
    .deck-exploded #slab-2 { transform: translateZ(-55px) !important; }
    .deck-exploded #slab-3 { transform: translateZ(-155px) !important; }

    .deck-exploded #slab-0.pulled-out { transform: translate3d(75px, 70px, 185px) scale3d(1.04, 1.04, 1.04) !important; }
    .deck-exploded #slab-1.pulled-out { transform: translate3d(75px, 70px, 85px) scale3d(1.04, 1.04, 1.04) !important; }
    .deck-exploded #slab-2.pulled-out { transform: translate3d(75px, 70px, -25px) scale3d(1.04, 1.04, 1.04) !important; }
    .deck-exploded #slab-3.pulled-out { transform: translate3d(75px, 70px, -125px) scale3d(1.04, 1.04, 1.04) !important; }

    .slab-layer .top {
        position: absolute;
        width: 230px;
        height: 230px;
        transform: translateZ(36px);
        box-shadow: inset 0 0 20px rgba(255, 255, 255, 0.25);
        transition: all 0.35s ease;
        backdrop-filter: blur(8px);
    }

    .slab-layer .front-right {
        position: absolute;
        width: 230px;
        height: 36px;
        bottom: 0;
        left: 0;
        transform-origin: bottom center;
        transform: rotateX(-90deg);
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: flex-end;
        padding-right: 14px;
        color: #FFFFFF;
        text-shadow: 0 1px 4px rgba(0, 0, 0, 0.9);
        transition: all 0.35s ease;
    }

    .slab-layer .front-left {
        position: absolute;
        width: 36px;
        height: 230px;
        top: 0;
        left: 0;
        transform-origin: left center;
        transform: rotateY(-90deg);
        transition: all 0.35s ease;
    }

    .slab-layer .back-right {
        position: absolute;
        width: 36px;
        height: 230px;
        top: 0;
        right: 0;
        transform-origin: right center;
        transform: rotateY(90deg);
        transition: all 0.35s ease;
    }

    .slab-layer .title-text {
        font-size: 11px;
        font-weight: 800;
        line-height: 1.2;
        letter-spacing: -0.01em;
    }

    .slab-layer .sub-text {
        font-size: 7.5px;
        font-weight: 500;
        opacity: 0.9;
        line-height: 1.2;
        letter-spacing: -0.01em;
    }

    /* Slab 0: No-Code Platform (Cyan) */
    #slab-0 .top {
        background: linear-gradient(135deg, rgba(2, 132, 199, 0.8) 0%, rgba(14, 165, 233, 0.45) 100%);
        border: 1.5px solid #00F0FF;
        box-shadow: inset 0 0 25px rgba(0, 240, 255, 0.4);
    }
    #slab-0 .front-right {
        background: linear-gradient(to right, #0369a1 0%, #0284c7 60%, #0369a1 100%);
        border-bottom: 2px solid #00F0FF;
    }
    #slab-0 .front-left {
        background: linear-gradient(to bottom, #075985 0%, #0369a1 100%);
    }
    #slab-0 .back-right {
        background: #0284c7;
    }

    /* Slab 1: Platform Services (Royal Blue) */
    #slab-1 .top {
        background: linear-gradient(135deg, rgba(29, 78, 216, 0.85) 0%, rgba(37, 99, 235, 0.5) 100%);
        border: 1.5px solid #3B82F6;
        box-shadow: inset 0 0 25px rgba(59, 130, 246, 0.4);
    }
    #slab-1 .front-right {
        background: linear-gradient(to right, #1e40af 0%, #1d4ed8 60%, #1e40af 100%);
        border-bottom: 2px solid #3B82F6;
    }
    #slab-1 .front-left {
        background: linear-gradient(to bottom, #172554 0%, #1e40af 100%);
    }
    #slab-1 .back-right {
        background: #1d4ed8;
    }

    /* Slab 2: Artificial Intelligence (Cyber Amber) */
    #slab-2 .top {
        background: linear-gradient(135deg, rgba(180, 83, 9, 0.85) 0%, rgba(245, 158, 11, 0.5) 100%);
        border: 1.5px solid #F59E0B;
        box-shadow: inset 0 0 25px rgba(245, 158, 11, 0.4);
    }
    #slab-2 .front-right {
        background: linear-gradient(to right, #92400e 0%, #b45309 60%, #92400e 100%);
        border-bottom: 2px solid #F59E0B;
    }
    #slab-2 .front-left {
        background: linear-gradient(to bottom, #78350f 0%, #92400e 100%);
    }
    #slab-2 .back-right {
        background: #b45309;
    }

    /* Slab 3: Data Lake & Core ERP (Emerald) */
    #slab-3 .top {
        background: linear-gradient(135deg, rgba(5, 150, 105, 0.85) 0%, rgba(16, 185, 129, 0.5) 100%);
        border: 1.5px solid #10B981;
        box-shadow: inset 0 0 25px rgba(16, 185, 129, 0.4);
    }
    #slab-3 .front-right {
        background: linear-gradient(to right, #065f46 0%, #059669 60%, #065f46 100%);
        border-bottom: 2px solid #10B981;
    }
    #slab-3 .front-left {
        background: linear-gradient(to bottom, #022c22 0%, #065f46 100%);
    }
    #slab-3 .back-right {
        background: #059669;
    }

    .slab-layer.pulled-out .top {
        border: 2px solid var(--active-accent, #00F0FF) !important;
        box-shadow: 0 0 35px var(--active-glow, rgba(0, 240, 255, 0.6)),
                    inset 0 0 20px var(--active-glow, rgba(0, 240, 255, 0.4)) !important;
    }
    .slab-layer.pulled-out .front-right {
        border-bottom: 2.5px solid var(--active-accent, #00F0FF) !important;
        text-shadow: 0 0 8px var(--active-accent, #00F0FF);
    }
    .slab-layer.pulled-out .front-left {
        border-bottom: 2.5px solid var(--active-accent, #00F0FF) !important;
    }

    .slab-shadow {
        position: absolute;
        width: 230px;
        height: 230px;
        transform: translateZ(-2px);
        background: rgba(0, 0, 0, 0.7);
        filter: blur(12px);
        transition: all 0.45s ease;
        pointer-events: none;
    }

    .slab-layer.pulled-out .slab-shadow {
        transform: translate3d(-20px, -20px, -18px);
        background: rgba(0, 0, 0, 0.5);
        filter: blur(20px);
    }

    .stage-hud-top {
        position: absolute;
        top: 20px;
        left: 20px;
        right: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        pointer-events: none;
        z-index: 10;
    }

    .badge-hud {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 6px;
        font-family: ui-monospace, monospace;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.05em;
        background: rgba(7, 11, 20, 0.85);
        color: #0ABBDB;
        border: 1px solid rgba(10, 187, 219, 0.35);
        backdrop-filter: blur(8px);
    }

    .stage-instruction {
        position: absolute;
        bottom: 16px;
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 11px;
        color: #64748B;
        font-family: ui-monospace, monospace;
        letter-spacing: 0.02em;
        pointer-events: none;
    }

    /* Right Description Column */
    .description-column {
        display: flex;
        flex-direction: column;
        justify-content: center;
        min-height: 520px;
    }

    .summary-card {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px 20px;
        display: flex;
        align-items: flex-start;
        gap: 16px;
        cursor: pointer;
        transition: all 0.25s ease;
        position: relative;
        backdrop-filter: blur(12px);

        &:hover, &.active-summary {
            background: rgba(15, 23, 42, 0.95);
            border-color: var(--card-color, #00F0FF);
            transform: translateX(6px);
            box-shadow: 0 8px 24px -4px var(--card-glow, rgba(0, 240, 255, 0.35));

            .card-title {
                color: var(--card-color, #00F0FF);
            }
        }
    }

    .card-icon-box {
        width: 44px;
        height: 44px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }

    .card-info {
        flex: 1;
    }

    .card-header-line {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 4px;
    }

    .card-title {
        font-size: 15px;
        font-weight: 700;
        color: #FFFFFF;
        transition: color 0.2s ease;
    }

    .card-layer-chip {
        font-size: 10px;
        font-weight: 700;
        font-family: ui-monospace, monospace;
        padding: 2px 8px;
        border-radius: 4px;
        background: var(--card-tint, rgba(0, 240, 255, 0.15));
        color: var(--card-color, #00F0FF);
        border: 1px solid var(--card-color, #00F0FF);
    }

    .card-desc {
        font-size: 12.5px;
        color: #94A3B8;
        line-height: 1.5;
        margin-bottom: 0;
    }

    /* Full Detailed Deep Panels */
    .deep-column-panel {
        background: rgba(11, 19, 36, 0.96);
        border: 1.5px solid var(--panel-color, #00F0FF);
        border-radius: 22px;
        padding: 28px;
        box-shadow: 0 20px 48px -8px var(--panel-glow, rgba(0, 240, 255, 0.35));
        animation: fadeInSlide 0.35s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        display: none;
        flex-direction: column;
        gap: 20px;
        backdrop-filter: blur(16px);

        &.visible {
            display: flex;
        }
    }

    .deep-header {
        display: flex;
        align-items: center;
        gap: 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding-bottom: 18px;
    }

    .deep-icon-large {
        width: 52px;
        height: 52px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FFFFFF;
        flex-shrink: 0;
        box-shadow: 0 8px 20px -4px rgba(0, 0, 0, 0.4);
    }

    .deep-title-group h3 {
        font-size: 20px;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: -0.02em;
    }

    .deep-title-group p {
        font-size: 12px;
        font-weight: 700;
        color: var(--panel-color, #0ABBDB) !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .deep-narrative {
        font-size: 13.5px;
        line-height: 1.6;
        color: #94A3B8 !important;
    }

    .deep-feature-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }

    .feature-pill {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px;
        transition: all 0.2s ease;

        &:hover {
            background: rgba(255, 255, 255, 0.06);
            border-color: var(--panel-color);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px -4px rgba(0, 0, 0, 0.3);
        }
    }

    .feature-pill-title {
        font-size: 13px;
        font-weight: 700;
        color: #FFFFFF !important;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 3px;
    }

    .feature-pill-desc {
        font-size: 11px;
        color: #94A3B8 !important;
        line-height: 1.4;
    }

    .tech-metrics-strip {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(255, 255, 255, 0.03);
        border: 1px dashed rgba(255, 255, 255, 0.15);
        border-radius: 12px;
        padding: 10px 16px;
        font-family: ui-monospace, monospace;
        font-size: 11px;
    }

    .metric-item {
        display: flex;
        flex-direction: column;
    }

    .metric-label {
        color: #64748B;
        font-size: 9px;
        text-transform: uppercase;
    }

    .metric-value {
        font-weight: 700;
        color: var(--panel-color);
        font-size: 13px;
    }

    .layer-selector-tabs {
        display: flex;
        gap: 8px;
        margin-top: 4px;
    }

    .tab-item {
        flex: 1;
        padding: 8px 6px;
        text-align: center;
        font-size: 11px;
        font-weight: 700;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.04);
        color: #94A3B8;
        cursor: pointer;
        transition: all 0.2s ease;

        &:hover, &.active {
            border-color: var(--tab-color);
            color: #FFFFFF !important;
            background: var(--tab-color);
            box-shadow: 0 0 12px var(--tab-color);
        }
    }

    .deck-footer {
        margin-top: 28px;
        padding-top: 18px;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        font-size: 12px;
        color: #64748B;
        font-family: ui-monospace, monospace;
    }

    .footer-left {
        display: flex;
        align-items: center;
        gap: 16px;
    }

    .footer-highlight {
        color: #0ABBDB;
        font-weight: 700;
    }
}

/* ==========================================================================
   INNORIA HERO VIDEO SLIDER WITH CINEMATIC TRANSITIONS & 4 PRODUCT THEMES
   ========================================================================== */
.innoria-hero-slider-section {
    position: relative;
    background: #070B14;
    min-height: 820px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
    padding-top: 60px;
    padding-bottom: 30px;

    /* Video Stage Background */
    .hero-video-stage {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        z-index: 0;
    }

    .video-slide-layer {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        opacity: 0;
        transform: scale(1.05);
        transition: opacity 1.1s cubic-bezier(0.16, 1, 0.3, 1), transform 8s cubic-bezier(0.1, 1, 0.1, 1);
        pointer-events: none;
        z-index: 1;

        &.active {
            opacity: 1;
            transform: scale(1.0);
            z-index: 2;
        }
    }

    /* Ambient Cinematic Dark Mask & Grid */
    .hero-cinematic-mask {
        position: absolute;
        inset: 0;
        background: 
            radial-gradient(ellipse at 50% 35%, rgba(7, 11, 20, 0.45) 0%, rgba(7, 11, 20, 0.82) 60%, #070B14 100%),
            linear-gradient(to bottom, rgba(7, 11, 20, 0.5) 0%, rgba(7, 11, 20, 0.88) 75%, #070B14 100%);
        z-index: 3;
        pointer-events: none;
    }

    .hero-grid-pattern {
        position: absolute;
        inset: 0;
        background-size: 40px 40px;
        background-image: 
            linear-gradient(to right, rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        z-index: 3;
        pointer-events: none;
    }

    .hero-ambient-glow {
        position: absolute;
        top: 20%;
        left: 50%;
        transform: translate(-50%, -20%);
        width: 700px;
        height: 450px;
        background: radial-gradient(circle, var(--hero-accent-glow, rgba(10, 187, 219, 0.18)) 0%, transparent 70%);
        filter: blur(40px);
        z-index: 3;
        pointer-events: none;
        transition: background 1s ease;
    }

    /* Content Stage */
    .hero-content-stage {
        position: relative;
        z-index: 5;
    }

    .hero-slide-item {
        display: none;
        opacity: 0;
        transform: translateY(20px);
        transition: opacity 0.5s ease, transform 0.5s cubic-bezier(0.16, 1, 0.3, 1);

        &.active {
            display: block;
            opacity: 1;
            transform: translateY(0);
        }
    }

    .hero-badge-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 6px 16px;
        border-radius: 9999px;
        font-family: ui-monospace, monospace;
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        font-weight: 700;
        background: rgba(11, 19, 36, 0.85);
        border: 1px solid var(--hero-accent, #00F0FF);
        color: var(--hero-accent, #00F0FF);
        box-shadow: 0 0 16px var(--hero-accent-glow, rgba(0, 240, 255, 0.3));
        backdrop-filter: blur(12px);
    }

    .hero-main-title {
        font-size: clamp(2.2rem, 4.5vw, 3.8rem);
        font-weight: 800;
        line-height: 1.15;
        letter-spacing: -0.02em;
        color: #FFFFFF;
    }

    .hero-gradient-text {
        background: var(--hero-gradient, linear-gradient(135deg, #0ABBDB 0%, #00F0FF 100%));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: inline-block;
    }

    .hero-lead-desc {
        font-size: clamp(1rem, 1.3vw, 1.25rem);
        line-height: 1.6;
        color: #94A3B8;
        max-width: 920px;
        margin: 0 auto;
    }

    /* Interactive Feature Chips */
    .hero-feature-chips-deck {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: center;
        gap: 10px;
        margin-top: 24px;
        margin-bottom: 28px;
    }

    .hero-feature-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        border-radius: 10px;
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #E2E8F0;
        font-size: 0.88rem;
        font-weight: 600;
        backdrop-filter: blur(12px);
        transition: all 0.25s ease;
        cursor: default;

        &:hover {
            background: rgba(15, 23, 42, 0.95);
            border-color: var(--hero-accent, #00F0FF);
            transform: translateY(-2px);
            box-shadow: 0 6px 18px -2px var(--hero-accent-glow, rgba(0, 240, 255, 0.3));
            color: #FFFFFF;
        }

        .chip-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--hero-accent, #00F0FF);
            box-shadow: 0 0 8px var(--hero-accent, #00F0FF);
        }
    }

    /* CTA Buttons */
    .hero-cta-btn-primary {
        background: var(--hero-gradient, linear-gradient(135deg, #0ABBDB 0%, #0284C7 100%));
        border: none;
        color: #FFFFFF;
        font-weight: 700;
        padding: 14px 32px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        box-shadow: 0 8px 24px var(--hero-accent-glow, rgba(10, 187, 219, 0.4));
        transition: all 0.25s ease;
        text-decoration: none;

        &:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 32px var(--hero-accent-glow, rgba(10, 187, 219, 0.6));
            color: #FFFFFF;
        }
    }

    .hero-cta-btn-secondary {
        background: rgba(11, 19, 36, 0.8);
        border: 1px solid var(--hero-accent, #0ABBDB);
        color: var(--hero-accent, #0ABBDB);
        font-weight: 700;
        padding: 14px 28px;
        border-radius: 9999px;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        backdrop-filter: blur(10px);
        transition: all 0.25s ease;
        text-decoration: none;

        &:hover {
            background: rgba(10, 187, 219, 0.15);
            color: #FFFFFF;
            transform: translateY(-2px);
        }
    }

    /* 4 Live Metric Tiles */
    .hero-metrics-deck {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 16px;
        margin-top: 36px;

        @media (max-width: 768px) {
            grid-template-columns: repeat(2, 1fr);
        }
    }

    .hero-metric-tile {
        background: rgba(11, 19, 36, 0.85);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 16px 20px;
        text-align: center;
        backdrop-filter: blur(12px);
        transition: all 0.3s ease;

        &:hover {
            border-color: var(--hero-accent, #0ABBDB);
            transform: translateY(-2px);
            box-shadow: 0 8px 24px -4px var(--hero-accent-glow, rgba(10, 187, 219, 0.25));
        }

        .metric-title {
            font-size: 0.75rem;
            font-weight: 600;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .metric-stat {
            font-size: 1.45rem;
            font-weight: 800;
            color: #FFFFFF;
            margin-top: 4px;
        }
    }

    /* Bottom 4-Product Segmented Navigation Bar */
    .hero-product-nav-bar {
        position: relative;
        z-index: 10;
        margin-top: 40px;
    }

    .hero-product-tabs-wrapper {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;

        @media (max-width: 992px) {
            grid-template-columns: repeat(2, 1fr);
        }
        @media (max-width: 576px) {
            grid-template-columns: 1fr;
        }
    }

    .hero-product-tab-btn {
        background: rgba(11, 19, 36, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 14px 18px;
        text-align: left;
        cursor: pointer;
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(14px);
        display: flex;
        flex-direction: column;
        justify-content: space-between;

        &:hover {
            background: rgba(15, 23, 42, 0.9);
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        &.active {
            background: rgba(15, 23, 42, 0.95);
            border-color: var(--tab-color, #00F0FF);
            box-shadow: 0 0 24px -4px var(--tab-glow, rgba(0, 240, 255, 0.35));

            .tab-index-tag {
                color: var(--tab-color, #00F0FF);
            }
            .tab-product-name {
                color: #FFFFFF;
            }
        }

        .tab-top-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 4px;
        }

        .tab-index-tag {
            font-family: ui-monospace, monospace;
            font-size: 0.72rem;
            font-weight: 700;
            color: #64748B;
            transition: color 0.2s ease;
        }

        .tab-category-label {
            font-size: 0.7rem;
            font-weight: 600;
            color: #94A3B8;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }

        .tab-product-name {
            font-size: 0.95rem;
            font-weight: 700;
            color: #CBD5E1;
            transition: color 0.2s ease;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        /* Animated Progress Line */
        .tab-progress-track {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: rgba(255, 255, 255, 0.06);
        }

        .tab-progress-fill {
            height: 100%;
            width: 0%;
            background: var(--tab-color, #00F0FF);
            box-shadow: 0 0 8px var(--tab-color, #00F0FF);
        }

        &.active .tab-progress-fill {
            transition: width 0.1s linear;
        }
    }

    /* Video Playback HUD Controls */
    .hero-slider-hud {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 12px;
        margin-top: 14px;
    }

    .hero-hud-btn {
        background: rgba(11, 19, 36, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.12);
        color: #94A3B8;
        border-radius: 8px;
        width: 34px;
        height: 34px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;

        &:hover {
            background: rgba(15, 23, 42, 0.95);
            border-color: #0ABBDB;
            color: #00F0FF;
        }
    }

    .hero-hud-counter {
        font-family: ui-monospace, monospace;
        font-size: 0.8rem;
        font-weight: 700;
        color: #94A3B8;
        padding: 0 8px;
    }
}
'''

with open(scss_path, 'w', encoding='utf-8') as f:
    f.write(base_content + new_scss + '\n')

print(f"Successfully updated {scss_path}")
