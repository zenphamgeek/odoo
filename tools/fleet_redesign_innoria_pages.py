#!/usr/bin/env python3
"""
tools/fleet_redesign_innoria_pages.py
=============================================================================
Orchestrates parallel redesign of all core Innoria website pages across 
AGY Fleet worker nodes.
Each page is researched from authentic innoria.com content and assigned 
to a dedicated high-capacity Fleet node to produce non-lazy, deep, 
production-ready QWeb XML templates.
=============================================================================
"""

import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.request

FLEET_API = "http://localhost:7777/api/fleet/run-sync"

PAGES_SPEC = [
    {
        "key": "about",
        "name": "Company / About Us",
        "template_id": "insilos_about_page",
        "url": "/about",
        "preferred_node": "pro-1",
        "content_file": "/tmp/innoria_company_content.txt",
        "prompt": """You are the Principal Enterprise Web Architect designing the official "Company / About Us" page for INNORIA (innoria.insilos.com).
Your design MUST be completely non-lazy, deep, comprehensive, and authentically reflect the identity, history, and culture of innoria.com.

BRAND IDENTITY & AUTHENTIC CONTEXT:
- Founded: 2008 as "Mạng Sáng Tạo" -> Rebranded and scaled to INNORIA (Over 18 years alongside technology: 2008-2026).
- Mission: Advance Vietnamese people and technology, delivering cutting-edge, user-friendly high-tech products worldwide.
- Core Culture: "Culture is something you cannot borrow, and the culture of our company is the harmonious accumulation of values, self-development, thoughts, and purpose."
  1. The intrinsic development of each member.
  2. Commitment to grow alongside the development of customers.
  3. Goals may change, but they always move forward.
- 4 Persona Segments (Create a rich, interactive 4-column card grid):
  1. Technology User: Experience Mojo AI for end users. Light, effortless AI integration.
  2. Innovation Business: State your operational bottleneck; we engineer tailored platform solutions.
  3. Software Deployment Partner: Seeking business expertise and strategic enterprise alliances.
  4. Technology Enthusiast: Research sandbox, open innovation community, advanced tech lab.
- Triad of Excellence (with quantifiable benchmarks):
  - Time: Accelerated development velocity; shorter time equals lower cost.
  - Cost: 50% reduction in deployment and operational expenses.
  - Quality: 18+ years of accumulated engineering rigor and ISO/SOC standards.
- Executive Leadership & Advisory Board:
  - Thang Pham: Founder & CEO ("Tradition and modernity, Eastern philosophy and Western technology... Yin and Yang.")
  - Do Thinh: Chief Technology Officer ("Organizations embracing blockchain are positioned to unlock efficiencies...")
  - Hoang Le: Mojo AI Division Head ("The brain needs to be brought into the body to get things done...")
  - Tham Mai: PMO & Industrial Solutions Head ("Streamlines inspection time and enhances accuracy...")
- Trust Factors: Long-standing culture, Vietnam 24/7 Support, Balanced cost & value.
- Client Trust Strip: Canva, Mobifone, Shinsei, AES, MTI, VNDIRECT, Eximbank, MUFG.
- Images: Use paths:
  - /insilos_website/static/src/img/innoria/team_advisory_photo.jpeg
  - /insilos_website/static/src/img/innoria/banner_digital_transformation.jpg
  - /insilos_website/static/src/img/innoria/client_a_gray.png
  - /insilos_website/static/src/img/innoria/client_b_gray.png
  - /insilos_website/static/src/img/innoria/client_d_gray.png

STYLING & ARCHITECTURE:
- Canvas: #111827 (Dark), Cards: #1F2937, Borders: rgba(255,255,255,0.08)
- Accents: Tech Cyan (#0ABBDB), Vivid Orange (#FF8000), Mint (#B2FFDA)
- Encapsulate in:
  <t t-call="website.layout" no_header="True" no_footer="True">
    <t t-call="insilos_website.innoria_navbar"/>
    <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas);">
      ... full content sections ...
    </main>
    <t t-call="insilos_website.innoria_footer"/>
  </t>

SECTIONS REQUIRED (Non-lazy, deep, comprehensive):
1. Hero Header: 18-Year Heritage (2008-2026), headline "Advancing People & Technology", verified impact stats.
2. The INNORIA Story & Heritage Timeline (2008 Mạng Sáng Tạo -> 2016 Enterprise Modernization -> 2022 AI & Web3 Labs -> 2026 INNORIA Platform).
3. Core Philosophy & Culture: 3 Guiding Tenets in elegant high-contrast dark cards.
4. 4 Persona Pathways: Engaging cards for Tech Users, Innovation Businesses, Deployment Partners, and Tech Enthusiasts.
5. Triad of Excellence: Time, Cost, and Quality comparison matrix.
6. Leadership & Global Engineering Team: Profile cards with authentic executive quotes.
7. Client Trust & Social Proof: Logo showcase and international delivery capability.
8. Executive CTA: Free 3-Hour Strategic Architecture Consultation.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML for the template. No markdown code blocks, no backticks, no explanatory chat outside the code. Start directly with <template id="insilos_about_page" name="About Us | INNORIA"> and end with </template>."""
    },
    {
        "key": "ai_platform",
        "name": "MOJO AI Platform",
        "template_id": "insilos_platform_page",
        "url": "/platform",
        "preferred_node": "nebula",
        "content_file": "/tmp/innoria_ai_platform_content.txt",
        "prompt": """You are the Principal AI & Enterprise Platform Architect designing the official "MOJO AI - Artificial Intelligence Platform" page for INNORIA (innoria.insilos.com).
Your design MUST be completely non-lazy, deep, comprehensive, and authentically reflect the identity of MOJO AI on innoria.com.

BRAND IDENTITY & AUTHENTIC CONTEXT:
- Headline: "MOJO AI — Intelligence, Cost-Saving, Efficient. One-stop AI Agent solutions builder."
- Quote from Hoang Le (Mojo AI Division Head):
  "The brain needs to be brought into the body to get things done, we balance in the study of Intelligence and portability of digital transformation."
- Scale & Validation: 700,000+ users across 200 countries (ai.mojo.vn).
- 4 Engagement Models (Interactive cards):
  1. Mojo AI as a Service (AaaS): Flexible pay-as-you-go and subscription models for individuals and fast-growing teams.
  2. Mojo AI in Digital Transformation: Enterprise-grade AI strategy, custom agent engineering, operational optimization.
  3. Mojo AI as Partners: OEM and ISV white-label AI agent integration for software vendors and consultancies.
  4. Mojo AI as a Platform: Foundational AI infrastructure for corporations building AI-native business models.
- Sector-Specific Applied AI in Digital Transformation:
  - Manufacturing: AI Reliability (predictive vibration & heat), AI Optical Counting, AI Inventory Optimization, Real-Time Defect Detection.
  - Telecom: AI Content Censorship (MobiFone video moderation benchmark), AI Customer Feedback Handling, Document Intelligence.
  - Energy & Utilities: AI PPE Detection, Fraud & Anomaly Detection, Substation Contractor FaceID.
- Generative AI & Vision Capabilities:
  - Gen Image, Gen QR Art, Gen Writer, Gen Voice, Ultra AI Vision.
- Images:
  - /insilos_website/static/src/img/innoria/importance_of_ai_services.webp
  - /insilos_website/static/src/img/innoria/coding_ai_nlp_data.jpg
  - /insilos_website/static/src/img/innoria/logo_innoria_eco_2.webp

STYLING & ARCHITECTURE:
- Canvas: #111827 (Dark), Cards: #1F2937, Accents: Tech Cyan (#0ABBDB), Vivid Orange (#FF8000), Mint (#B2FFDA)
- Encapsulate in:
  <t t-call="website.layout" no_header="True" no_footer="True">
    <t t-call="insilos_website.innoria_navbar"/>
    <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas);">
      ... full content sections ...
    </main>
    <t t-call="insilos_website.innoria_footer"/>
  </t>

SECTIONS REQUIRED:
1. Hero Section: "MOJO AI: One-stop AI Agent Solutions Builder", global scale badge (700K+ users | 200 countries), interactive AI Agent prompt demo console.
2. Hoang Le Executive Quote Feature: Stylized quote card with division credentials.
3. 4 Engagement Models: Deep architectural breakdown with SLA, compute tiers, and deployment options.
4. Sector Solutions Matrix: Tabbed or grid layout for Manufacturing, Telecom, and Energy.
5. Generative AI & Multimodal Studio: Feature breakdown of Image, Voice, Text, and Vision engines.
6. Real-Time AI Agent Telemetry HUD: Live simulated latency, token velocity, and accuracy metrics.
7. CTA Section: Schedule an AI Agent Architectural Audit.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML for the template. No markdown code blocks, no backticks, no explanatory chat outside the code. Start directly with <template id="insilos_platform_page" name="MOJO AI Platform | INNORIA"> and end with </template>."""
    },
    {
        "key": "no_code",
        "name": "DIGIFORCE No-Code Platform",
        "template_id": "innoria_digiforce_page",
        "url": "/no-code-platform",
        "preferred_node": "ultra-2",
        "content_file": "/tmp/innoria_no_code_content.txt",
        "prompt": """You are the Principal Enterprise Software Architect designing the official "DIGIFORCE — High-Performance Low-Code Platform" page for INNORIA (innoria.insilos.com).
Your design MUST be completely non-lazy, deep, comprehensive, and authentically reflect the identity of DIGIFORCE on innoria.com.

BRAND IDENTITY & AUTHENTIC CONTEXT:
- Headline: "DIGIFORCE — High-Performance Low-Code Platform. No more struggling with software — simply work with your AI assistant."
- Quote from Thang Pham (INNORIA Founder):
  "DIGIFORCE – a low-code platform that rapidly develops software in weeks, max 3 months. Delivering exceptional cost efficiency while meeting the unique needs of every business."
- Proven Empirical Numbers:
  - Velocity: Tailored enterprise software delivered in weeks, maximum 3 months.
  - Cost Reduction: 50% decrease in overall development and maintenance expenditure.
  - Team Multiplication: Solution delivery capacity doubled without adding headcount.
  - Multi-Tech Fusion: Low-Code + AI + RPA + Blockchain unified into a single runtime.
- Real-World Solution Modules:
  - Digital Transformation: Enterprise Resource Planning, Intelligent Logistics Management, Certificate of Origin (C/O) Automation, Contractor Management.
  - Governance, Risk & Compliance (GRC): Health Safety Environment (HSE), Digital Operation Rounds, Permit to Work (e-PTW), Virtual Risk Assessment.
  - Innovation: Low-code plus AI agents, Low-code plus Smart Contracts.
- Images:
  - /insilos_website/static/src/img/innoria/group_52424.webp (DIGIFORCE Robot Icon)
  - /insilos_website/static/src/img/innoria/banner_digital_transformation.jpg

STYLING & ARCHITECTURE:
- Canvas: #111827 (Dark), Cards: #1F2937, Accents: Tech Cyan (#0ABBDB), Vivid Orange (#FF8000), Emerald (#10B981)
- Encapsulate in:
  <t t-call="website.layout" no_header="True" no_footer="True">
    <t t-call="insilos_website.innoria_navbar"/>
    <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas);">
      ... full content sections ...
    </main>
    <t t-call="insilos_website.innoria_footer"/>
  </t>

SECTIONS REQUIRED:
1. Hero Header: "DIGIFORCE: Enterprise Software in Weeks, Not Years", Thang Pham quote badge, interactive visual app canvas mockup.
2. DIGIFORCE in Numbers: 4 Hero KPI tiles (-50% Cost, 3-Month Max Delivery, 2x Velocity, 100% Extensible).
3. Why Low-Code Saves You: Traditional Code vs DIGIFORCE side-by-side comparison table.
4. Core Solution Suites:
   - Digital Transformation Suite (ERP, Logistics, C/O, Contractor).
   - GRC & Industrial Safety Suite (HSE, Operation Round, e-PTW, Risk Assessment).
5. Multi-Tech Fusion Engine: Visual architecture showing how AI, RPA, and Blockchain seamlessly plug into DIGIFORCE drag-and-drop workflows.
6. Interactive Workflow Builder Simulation: Visual node-based workflow diagram.
7. Executive CTA: Free 3-Hour Prototyping Workshop.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML for the template. No markdown code blocks, no backticks, no explanatory chat outside the code. Start directly with <template id="innoria_digiforce_page" name="DIGIFORCE No-Code Platform | INNORIA"> and end with </template>."""
    },
    {
        "key": "blockchain",
        "name": "MOJOVERSE Blockchain Platform",
        "template_id": "innoria_blockchain_page",
        "url": "/blockchain",
        "preferred_node": "9router",
        "content_file": "/tmp/innoria_blockchain_content.txt",
        "prompt": """You are the Principal Web3 & Distributed Systems Architect designing the official "MOJOVERSE — Enterprise Blockchain Platform" page for INNORIA (innoria.insilos.com).
Your design MUST be completely non-lazy, deep, comprehensive, and authentically reflect the identity of MOJOVERSE on innoria.com.

BRAND IDENTITY & AUTHENTIC CONTEXT:
- Headline: "Capitalize on Emerging Blockchain. Revolutionizing data management, trust, and transparency."
- Quote from Do Thinh (CTO - INNORIA):
  "Organizations embracing blockchain are positioned to unlock efficiencies, reduce costs in the digital economy."
- Quote from Thang Pham (CEO - INNORIA):
  "Tradition and modernity, Eastern philosophy and Western technology, law and freedom, rigor and fluidity, interior and exterior... Yin and Yang."
- 4 Foundational Pillars:
  1. Digital Identity & Authentication (DID): Self-sovereign identity, biometric cryptographic claims, verifiable credentials.
  2. Business Models & Tokenomics: Real World Asset (RWA) tokenization, fractional ownership, dynamic liquidity.
  3. Decentralized Finance (DeFi) for Enterprises: Peer-to-peer enterprise escrow, algorithmic clearing, automated treasury management.
  4. Cryptographic Data Security & Immutable Ledger: Tamper-proof auditing, zero-knowledge verification, enterprise permissioned networks.
- Supply Chain Optimization & Smart Contracts: Real-time end-to-end provenance, anti-counterfeiting, digital Certificate of Origin (e-CO) verification.
- Images:
  - /insilos_website/static/src/img/innoria/logo_innoria_eco_1.webp (MOJOVERSE Icon)
  - /insilos_website/static/src/img/innoria/architecture_innoria_platform_grey.svg

STYLING & ARCHITECTURE:
- Canvas: #111827 (Dark), Cards: #1F2937, Accents: Tech Cyan (#0ABBDB), Vivid Orange (#FF8000), Cyber Violet (#8B5CF6)
- Encapsulate in:
  <t t-call="website.layout" no_header="True" no_footer="True">
    <t t-call="insilos_website.innoria_navbar"/>
    <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas);">
      ... full content sections ...
    </main>
    <t t-call="insilos_website.innoria_footer"/>
  </t>

SECTIONS REQUIRED:
1. Hero Header: "MOJOVERSE: Enterprise-Grade Trust & Real-World Asset Tokenization", CTO Do Thinh quote banner.
2. Eastern Philosophy meets Western Technology: Thang Pham's "Yin & Yang" architectural paradigm feature card.
3. 4 Pillar Breakdown: DID, Tokenomics & RWA, Enterprise DeFi, Immutable Ledger.
4. Smart Contract & Supply Chain Traceability Engine: Interactive step-by-step verification pipeline (Manufacturer -> Logistics -> Customs -> Distributor -> Consumer).
5. Enterprise Architecture Diagram & Security Specifications (Multi-chain compatibility, EVM/Substrate, Zero-Knowledge proofs).
6. Live Block Explorer & Ledger Simulator HUD: Visual block feed showing simulated transactions, cryptographic hashes, and consensus status.
7. CTA: Request an Enterprise Web3 Architecture Assessment.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML for the template. No markdown code blocks, no backticks, no explanatory chat outside the code. Start directly with <template id="innoria_blockchain_page" name="MOJOVERSE Blockchain Platform | INNORIA"> and end with </template>."""
    },
    {
        "key": "erp_ai",
        "name": "AI-Enhanced ERP & Solutions",
        "template_id": "insilos_solutions_page",
        "url": "/solutions",
        "preferred_node": "insilos",
        "content_file": "/tmp/innoria_erp_ai_content.txt",
        "prompt": """You are the Principal Enterprise ERP & AI Solutions Architect designing the official "AI-Enhanced ERP & Solutions" page for INNORIA (innoria.insilos.com).
Your design MUST be completely non-lazy, deep, comprehensive, and authentically reflect the identity of AI-Enhanced ERP on innoria.com.

BRAND IDENTITY & AUTHENTIC CONTEXT:
- Headline: "AI-Enhanced ERP — Block the Noise. Build Freely. No more struggling with software — simply work with your AI assistant."
- Quote from Hoang Le (Mojo AI Division Head):
  "Essentially, AI augments ERP capabilities, transforming raw data into strategic intelligence and driving smarter, more agile business operations."
- Core Problems Solved:
  1. Learn software effortlessly: Conversational natural language interface replacing complex navigation menus.
  2. Automatic Data Ingestion: Excel spreadsheets, paper invoices, and unstructured emails automatically ingested into ledger records.
  3. Unified Cross-Silo Intelligence: Ask AI across CRM, Manufacturing, Inventory, and Financials simultaneously.
  4. Autonomous Purchasing: Demand forecasting, automatic vendor RFQ evaluation, and purchase order drafting.
  5. Intelligent Sales Assistant: Multi-channel lead qualification, automated pricing calculation, and 24/7 instant client support.
- Predefined Enterprise Workflows:
  - 3-Way Invoice & PO Matching with Circular 78 / Decree 123 E-Invoice integration.
  - Multi-level BOM optimization and MRP scheduling.
  - Predictive stock reordering and warehouse storage balancing.
- Images:
  - /insilos_website/static/src/img/innoria/importance_of_ai_services.webp
  - /insilos_website/static/src/img/innoria/coding_ai_nlp_data.jpg
  - /insilos_website/static/src/img/innoria/architecture_innoria_platform_grey.svg

STYLING & ARCHITECTURE:
- Canvas: #111827 (Dark), Cards: #1F2937, Accents: Tech Cyan (#0ABBDB), Vivid Orange (#FF8000), Safety Yellow (#F59E0B)
- Encapsulate in:
  <t t-call="website.layout" no_header="True" no_footer="True">
    <t t-call="insilos_website.innoria_navbar"/>
    <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas);">
      ... full content sections ...
    </main>
    <t t-call="insilos_website.innoria_footer"/>
  </t>

SECTIONS REQUIRED:
1. Hero Header: "AI-Enhanced ERP: Work Feels Lighter", Hoang Le quote badge, conversational AI co-pilot prompt card.
2. The 5 Autonomous Superpowers: Cards for Natural Language ERP, Auto Ingestion, Cross-Silo Querying, Auto Purchasing, and Sales Bot.
3. Legacy ERP vs Innoria AI ERP: Side-by-side comparison matrix (Speed, Learning Curve, Error Rate, TCO).
4. Predefined AI Workflow Showcases: Interactive tabbed view (Procure-to-Pay, Order-to-Cash, Plan-to-Produce, Record-to-Report).
5. Executive Control Tower Dashboard HUD: Visual cards showing real-time OEE (92%+), OTIF (98.5%+), and Cash Flow.
6. Client Success Stories: Real-world results with logistics hubs, manufacturing plants, and trading companies.
7. CTA: Book a Live 3-Hour AI ERP Proof of Concept.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML for the template. No markdown code blocks, no backticks, no explanatory chat outside the code. Start directly with <template id="insilos_solutions_page" name="AI-Enhanced ERP | INNORIA"> and end with </template>."""
    },
    {
        "key": "ultra_ai_vision",
        "name": "Ultra AI Vision & Industry Solutions",
        "template_id": "insilos_industries_page",
        "url": "/industries",
        "preferred_node": "codegeekvn",
        "content_file": "/tmp/innoria_ultra_ai_vision_content.txt",
        "prompt": """You are the Principal Computer Vision & Smart Manufacturing Architect designing the official "Ultra AI Vision & Industry Solutions" page for INNORIA (innoria.insilos.com).
Your design MUST be completely non-lazy, deep, comprehensive, and authentically reflect the identity of Ultra AI Vision on innoria.com.

BRAND IDENTITY & AUTHENTIC CONTEXT:
- Headline: "ULTRA AI VISION — Superior Defect Detection, Item Classification, Optical Character Recognition."
- Quote from Tham Mai (PMO Division Head):
  "Streamlines inspection time and enhances accuracy, surpassing manual methods and older systems to help manufacturers consistently achieve top-quality standards."
- 4 Proven Real-World Projects:
  1. Shrimp Seed Counting (Thủy hải sản): High-speed automated juvenile shrimp counting with 99.4% precision under turbulent water conditions.
  2. Analog Instrument & Gauge Reading (Đồng hồ cơ khí): Digitize legacy analog dials, pressure gauges, and meters using existing standard CCTV cameras.
  3. Parking & Vehicle Management System: High-speed ANPR license plate recognition, multi-lane barrier control, real-time occupancy tracking.
  4. High-Speed Object Counting: Precision verification for high-throughput packaging, logistics sorting, and container staging.
- Technical Advantages (We Bring):
  - Few-Shot Data Learning: Train high-precision inspection models from as few as 1-5 image samples.
  - Quick Model Training: Train bespoke models in minutes via Mojo Data Studio with adjustable parameter sizes.
  - Industrial Camera & Hardware Integration: Native PLC communications via TCP/IP and Modbus protocols included out-of-the-box.
- Key Industry Verticals:
  - Manufacturing: Defect detection, assembly verification, dimensional measurement, barcode & label verification.
  - Textiles & Garments: Fabric flaw inspection, pattern matching, color consistency monitoring, seam & stitch inspection.
  - Electronics: High-precision PCB inspection, component placement verification, solder joint quality analysis.
  - Energy & Construction: EHS / PPE Compliance detection (helmets, high-vis vests, eyewear), dangerous zone intrusion.
- Images:
  - /insilos_website/static/src/img/innoria/coding_ai_nlp_data.jpg
  - /insilos_website/static/src/img/innoria/importance_of_ai_services.webp

STYLING & ARCHITECTURE:
- Canvas: #111827 (Dark), Cards: #1F2937, Accents: Tech Cyan (#0ABBDB), Vivid Orange (#FF8000), Neon Green (#00F0FF)
- Encapsulate in:
  <t t-call="website.layout" no_header="True" no_footer="True">
    <t t-call="insilos_website.innoria_navbar"/>
    <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas);">
      ... full content sections ...
    </main>
    <t t-call="insilos_website.innoria_footer"/>
  </t>

SECTIONS REQUIRED:
1. Hero Header: "Ultra AI Vision: Sub-Millimeter Inspection & Automated Counting", Tham Mai quote badge, simulated computer vision inspection HUD with bounding boxes and confidence score overlay.
2. 4 Real-World Landmark Projects: Deep technical case cards for Shrimp Seed Counting, Analog Gauge Reading, Parking ANPR, and High-Speed Object Counting.
3. Technical Superiority: Few-Shot (1-5 samples), Quick Training (Mojo Data Studio), and Hardware Interoperability (PLC / Modbus).
4. Vertical Industry Solutions Matrix: Interactive tabbed cards for Manufacturing, Textiles, Electronics, and Energy/EHS.
5. Interactive Inspection Simulator: Visual before/after defect analysis card with heatmap overlay.
6. Architecture & Camera Deployment: Edge AI deployment specs (NPU/GPU edge gateways, IP cameras, zero latency inference).
7. CTA: Request an On-Site Computer Vision Pilot.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML for the template. No markdown code blocks, no backticks, no explanatory chat outside the code. Start directly with <template id="insilos_industries_page" name="Ultra AI Vision &amp; Industries | INNORIA"> and end with </template>."""
    },
    {
        "key": "contactus",
        "name": "Contact Us & Executive Advisory",
        "template_id": "website.contactus",
        "url": "/contactus",
        "preferred_node": "binhthuong",
        "content_file": "/tmp/innoria_contactus_content.txt",
        "prompt": """You are the Principal UX & Executive Engagement Architect designing the official "Contact Us & Executive Consultation" page for INNORIA (innoria.insilos.com).
Your design MUST be completely non-lazy, deep, comprehensive, and authentically reflect the identity of innoria.com.

BRAND IDENTITY & AUTHENTIC CONTEXT:
- Headline: "Ready to Bring Your Digital Vision to Life? Let's collaborate to create innovative solutions that stand out."
- Free 3-Hour Executive Strategic Architecture Workshop (Phiên tư vấn kiến trúc ban đầu hoàn toàn miễn phí).
- Authentic Corporate Coordinates:
  - Corporate Entity: UNG DUNG SANG TAO LLC (Công Ty TNHH Ứng Dụng Sáng Tạo)
  - Tax ID / Giấy phép kinh doanh: 0313683499
  - Headquarters: 45 street 3, Trung Son Resident, Binh Hung ward, Binh Chanh district, Ho Chi Minh city, Vietnam (45 đường số 3, KDC Trung Sơn, Xã Bình Hưng, Huyện Bình Chánh, TP. Hồ Chí Minh).
  - Official Inquiries: contact@innoria.com
- Global Hubs & Advisory Offices:
  - Ho Chi Minh City (R&D & Headquarters)
  - Hanoi (Government & Enterprise Consulting)
  - Tokyo, Japan (Regional Partner Operations)
  - Singapore (Capital Markets & Web3 Alliances)
- Service Commitments (SLAs):
  - 100% response within 2 business hours.
  - Strict Enterprise NDA signed prior to architectural discovery.
  - Zero proprietary lock-in: You own 100% of your data and business logic.
- Images:
  - /insilos_website/static/src/img/innoria/innoria_logo_grayscale.svg
  - /insilos_website/static/src/img/innoria/logo_innoria_header.svg

STYLING & ARCHITECTURE:
- Canvas: #111827 (Dark), Cards: #1F2937, Accents: Tech Cyan (#0ABBDB), Vivid Orange (#FF8000), Mint (#B2FFDA)
- Encapsulate in:
  <t t-call="website.layout" no_header="True" no_footer="True">
    <t t-call="insilos_website.innoria_navbar"/>
    <main id="wrap" class="oe_structure o_colored_level o_cc o_cc5" style="background-color: var(--innoria-dark-canvas);">
      ... full content sections ...
    </main>
    <t t-call="insilos_website.innoria_footer"/>
  </t>

SECTIONS REQUIRED:
1. Hero Header: "Let's Build Something Extraordinary Together", 3-Hour Free Architecture Consultation highlight badge.
2. The 3-Hour Executive Consultation Blueprint: What happens during the session (Problem Definition -> Technical Feasibility -> Architecture Roadmap -> Pilot Scope).
3. Executive Consultation Booking Form: Polished dark form with Name, Corporate Email, Phone, Company, Solution of Interest (DIGIFORCE / MOJO AI / MOJOVERSE / AI ERP / Ultra Vision), Target Timeline, and Project Description.
4. Corporate Office Coordinates & Interactive Location Cards: Headquarters in Trung Son, HCMC, plus Hanoi, Tokyo, and Singapore hubs.
5. Trust & Compliance Guarantees: ISO 27001, SOC-2 readiness, NDA guarantee, SLA response badge.
6. FAQ & Pre-Engagement Checklist: 4 essential questions answered for CIOs and CTOs.

OUTPUT FORMAT:
Return ONLY the raw QWeb XML for the template. No markdown code blocks, no backticks, no explanatory chat outside the code. Start directly with <template id="website.contactus" name="Contact Us | INNORIA"> and end with </template>."""
    }
]

def call_fleet_node(spec):
    key = spec["key"]
    node = spec["preferred_node"]
    prompt = spec["prompt"]
    print(f"[*] Dispatching Page [{spec['name']}] to Fleet Node [{node}]...")
    
    payload = {
        "prompt": prompt,
        "model": "gemini-3.8-flash-high",
        "node_name": node,
        "timeout": 240
    }
    
    req = urllib.request.Request(
        FLEET_API,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=250) as res:
            resp_data = json.loads(res.read().decode("utf-8"))
            elapsed = time.time() - start_t
            exec_node = resp_data.get("node_name", node)
            raw_output = resp_data.get("output") or resp_data.get("clean_response") or ""
            print(f"[✓] Page [{spec['name']}] completed by Node [{exec_node}] in {elapsed:.1f}s ({len(raw_output)} chars)")
            return {
                "key": key,
                "spec": spec,
                "node": exec_node,
                "elapsed": elapsed,
                "raw_output": raw_output,
                "error": None
            }
    except Exception as e:
        elapsed = time.time() - start_t
        print(f"[✗] Page [{spec['name']}] on Node [{node}] failed after {elapsed:.1f}s: {e}")
        return {
            "key": key,
            "spec": spec,
            "node": node,
            "elapsed": elapsed,
            "raw_output": "",
            "error": str(e)
        }

def clean_xml_output(raw_output, template_id, template_name):
    # Extract code between ```xml ... ``` or ``` ... ``` if present
    code_match = re.search(r"```(?:xml)?\s*(.*?)\s*```", raw_output, re.DOTALL)
    if code_match:
        content = code_match.group(1).strip()
    else:
        content = raw_output.strip()
    
    # Ensure template tag wraps the content correctly
    if f'<template id="{template_id}"' not in content and f"<template id='{template_id}'" not in content:
        # Wrap if missing
        content = f'<template id="{template_id}" name="{template_name}">\n{content}\n</template>'
    
    # Remove any stray markdown or invalid text before <template
    template_start = content.find("<template")
    if template_start != -1:
        content = content[template_start:]
    template_end = content.rfind("</template>")
    if template_end != -1:
        content = content[:template_end + len("</template>")]
        
    return content

def main():
    print(f"=== INNORIA AGY FLEET PARALLEL REDESIGN (7 PAGES) ===")
    print(f"Fleet Endpoint: {FLEET_API}")
    print(f"Pages to redesign: {len(PAGES_SPEC)}")
    for p in PAGES_SPEC:
        print(f"  - [{p['name']}] -> Target Node: {p['preferred_node']}")
    print("=" * 60)
    
    start_total = time.time()
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=7) as executor:
        future_to_page = {executor.submit(call_fleet_node, spec): spec for spec in PAGES_SPEC}
        for future in concurrent.futures.as_completed(future_to_page):
            res = future.result()
            results[res["key"]] = res
            
    total_elapsed = time.time() - start_total
    print("=" * 60)
    print(f"All 7 Fleet jobs completed in {total_elapsed:.1f}s.")
    
    # Save results to scratch / tmp
    os.makedirs("/tmp/innoria_fleet_results", exist_ok=True)
    success_count = 0
    for key, res in results.items():
        if res["error"] or not res["raw_output"]:
            print(f"[!] Warning: Page {key} encountered error: {res['error']}")
        else:
            success_count += 1
            cleaned_xml = clean_xml_output(res["raw_output"], res["spec"]["template_id"], res["spec"]["name"])
            out_file = f"/tmp/innoria_fleet_results/{key}.xml"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(cleaned_xml)
            print(f"[✓] Saved cleaned XML for {key} -> {out_file} ({len(cleaned_xml)} chars)")
            
    print(f"Summary: {success_count}/{len(PAGES_SPEC)} pages generated successfully by Fleet.")
    return 0 if success_count == len(PAGES_SPEC) else 1

if __name__ == "__main__":
    sys.exit(main())
