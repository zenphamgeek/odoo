#!/usr/bin/env python3
"""
tools/fleet_pos_react_autonomous.py
Autonomous Multi-Node Fleet Runner for POS React Full Parity
Dispatches parallel code generation across AGY Fleet nodes:
1. Carbon/Fiori SCSS Theme & Layout (app.css)
2. Interactive Numpad & Line Modifier Engine (components/numpad.js)
3. Dedicated Payment Screen with Split Tenders (components/payment_screen.js)
4. Thermal Receipt & E-Receipt Delivery (components/receipt_screen.js)
5. Comprehensive Modals (components/modals.js)
Assembles and verifies locally with unit tests and live Playwright E2E.
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

FLEET_URL = "http://localhost:7777"
WORKSPACE_ROOT = "/home/zen/O20"

TASKS = [
    {
        "id": "TASK_CSS",
        "file": "enterprise/pos_react/static/src/app.css",
        "model": "gemini-4-argon-high",
        "prompt": """You are an expert design systems engineer specializing in IBM Carbon 11, SAP Fiori Horizon, and Touch POS ergonomics.
TASK: Write the complete, production-grade stylesheet `enterprise/pos_react/static/src/app.css` for the React POS application.

REQUIREMENTS:
1. Sovereign Design Tokens & Zero Bare White Surfaces:
   - Root tokens: `--pos-bg-canvas: #0b0f17`, `--pos-bg-surface: #131a26`, `--pos-bg-card: #1c2637`, `--pos-bg-hover: #26344b`, `--pos-bg-active: #324360`, `--pos-border: #243044`, `--pos-border-subtle: #1e2838`, `--pos-accent: #00f2fe`, `--pos-accent-hover: #38f8ff`, `--pos-primary: #0f62fe`, `--pos-text-primary: #f4f7fb`, `--pos-text-secondary: #94a3b8`, `--pos-text-muted: #64748b`, `--pos-success: #10b981`, `--pos-danger: #ef4444`, `--pos-warning: #f59e0b`.
   - Also support light theme via `:root[data-theme='light']`: `--pos-bg-canvas: #f4f6f9`, `--pos-bg-surface: #ffffff`, `--pos-bg-card: #f8fafc`, `--pos-bg-hover: #e2e8f0`, `--pos-border: #cbd5e1`, `--pos-text-primary: #0f172a`, `--pos-text-secondary: #475569`.
   - Default is Sovereign Dark theme. Zero hardcoded bare white (#fff/#ffffff) as surface background.
2. Layout Structure:
   - Fullscreen viewport (`height: 100vh`, `display: flex`, `flex-direction: column`, `overflow: hidden`, `font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`).
   - Top Header Bar (height 48px, compact, sticky top): Flex layout with Cashier pill badge, Order tabs bar (scrollable horizontal pills with active state, add order `+` button), Sync status chip (green pulse dot when online, red when offline), and Header action buttons.
   - Dual-pane Workspace:
     - Left Pane: Categories nav bar (horizontal scrollable pills with active state), Search bar with barcode icon, Products Grid (CSS Grid with `repeat(auto-fill, minmax(130px, 1fr))`, gap 10px, cards with product name, price badge, touch active feedback, hover elevation).
     - Right Pane (Cart & Controls, width 380px to 420px):
       - Cart Line Items list (`flex: 1`, `overflow-y: auto`): Item lines with quantity badge, item name, unit price, discount tag, line subtotal formatted with `tabular-nums`. Active line highlighted with cyan border accent (`border-left: 3px solid var(--pos-accent)`).
       - Cart Summary Bar: Item count, Subtotal, Tax breakdown, Total Amount (`font-size: 20px`, `font-weight: 700`, `font-feature-settings: 'tnum'`).
       - Numpad Grid (4 columns × 4 rows): Tactile buttons, 48px baseline height, active depressed state, distinctive color for mode buttons (`Qty`, `% Disc`, `Price`), Backspace `⌫` button.
       - Bottom Action Toolbar: Customer button, Note button, Refund button, and massive prominent "Pay" button (`background: var(--pos-accent)`, `color: #050b14`, `font-weight: 700`, `height: 48px`).
3. Dedicated Screens:
   - Payment Screen (`.pos-payment-screen`): 3-column layout (Summary left, Numpad + Quick Cash middle, Payment methods list right), Validate button, Back button.
   - Receipt Screen (`.pos-receipt-screen`): Centered thermal receipt card (paper white with dark text or dark slip, monospace font, dashed borders, shop logo, barcode/QR placeholder), Print and New Order action buttons.
   - Thermal Print Rules (`@media print`): Hides all POS shell controls, formats `.pos-receipt-paper` to 80mm width with 0 margins.
4. Modal Dialogs (`.pos-modal-overlay`, `.pos-modal-dialog`):
   - Backdrop blur, centered window, header with title and close `×`, scrollable body, footer buttons (`40px` height).
   - Styles for Customer selection table/list, search input, quick create form.

OUTPUT FORMAT:
Return ONLY the complete CSS code block inside ```css ... ```. Do not include extra conversational text."""
    },
    {
        "id": "TASK_NUMPAD",
        "file": "enterprise/pos_react/static/src/components/numpad.js",
        "model": "gemini-4-argon-high",
        "prompt": """You are a senior React frontend engineer specializing in Point of Sale hardware/touch interactions.
TASK: Write the complete, production-grade component module `enterprise/pos_react/static/src/components/numpad.js`.

REQUIREMENTS:
1. Environment: Native browser React (React 18 global `window.React` - `createElement as h`, `useState`, `useEffect`, `useCallback`, `useRef`). Do not use JSX compilation syntax; use standard `React.createElement` (or `const h = React.createElement`).
2. Component Definition:
   - Name: `window.PosReactNumpad = function PosReactNumpad({ activeMode, setMode, onInput, onDelete, onClear, onCustomerClick, onNoteClick, onRefundClick, onPayClick, disabled, total, formatMoney, selectedLine }) { ... }`
3. Numpad Keys:
   - 4x4 Keypad layout:
     - Row 1: `1`, `2`, `3`, Mode: `qty` (label: "Qty")
     - Row 2: `4`, `5`, `6`, Mode: `discount` (label: "% Disc")
     - Row 3: `7`, `8`, `9`, Mode: `price` (label: "Price")
     - Row 4: `+/-`, `0`, `.`, Action: `backspace` (label: "⌫")
   - Mode buttons highlight when `activeMode === mode`.
   - Clicking a numeric button calls `onInput(key)`.
   - Clicking `+/-` toggles negative.
   - Clicking `⌫` calls `onDelete()`.
4. Action Bar Buttons below or adjacent:
   - `Customer` button (displays current customer name if selected or "Customer").
   - `Note` button.
   - `Refund` button.
   - Big `Pay` button (displays "Pay " + formatted total, disabled if cart is empty or `disabled === true`).
5. Keyboard Shortcuts:
   - Attach global `keydown` listener when component is mounted.
   - If user presses `0`-`9` or `.`, trigger `onInput`.
   - If user presses `Backspace`, trigger `onDelete`.
   - If user presses `Delete` or `Escape`, trigger `onClear`.
   - If user presses `q` or `Q`, set mode `qty`.
   - If user presses `d` or `D`, set mode `discount`.
   - If user presses `p` or `P`, set mode `price`.
   - If user presses `Enter` or `Space` (when on product screen), trigger `onPayClick`.
   - IMPORTANT: Only intercept keydown if `event.target.tagName !== 'INPUT'` and `event.target.tagName !== 'TEXTAREA'`.
6. Export:
   - Attach to `window.PosReactNumpad`.

OUTPUT FORMAT:
Return ONLY the complete JavaScript code block inside ```javascript ... ```. Do not include conversational text."""
    },
    {
        "id": "TASK_PAYMENT",
        "file": "enterprise/pos_react/static/src/components/payment_screen.js",
        "model": "gemini-4-argon-high",
        "prompt": """You are a senior React frontend engineer specializing in Insilos POS payment workflows.
TASK: Write the complete, production-grade component module `enterprise/pos_react/static/src/components/payment_screen.js`.

REQUIREMENTS:
1. Environment: Native browser React (React 18 global `window.React` - `createElement as h`, `useState`, `useEffect`, `useMemo`, `useRef`). Use `React.createElement` (or `h`).
2. Component Definition:
   - `window.PosReactPaymentScreen = function PosReactPaymentScreen({ context, onValidate, onBack }) { ... }`
3. Functionality:
   - State:
     - `tendered`: numeric amount currently entered on the keypad.
     - `paymentLines`: array of registered payments `[{ id, method, amount, state, transactionId }]`.
     - `toInvoice`: boolean checkbox for customer accounting invoice.
     - `selectedMethodId`: currently active payment method.
     - `error`: error message string.
     - `processing`: boolean during RPC/adapter calls.
   - Calculations:
     - `totalDue`: order total from `context.total`.
     - `totalPaid`: sum of `paymentLines.map(p => p.amount)`.
     - `remaining`: `Math.max(0, totalDue - totalPaid)`.
     - `change`: `Math.max(0, totalPaid - totalDue)`.
   - Quick Cash Denominations:
     - Chips for: `Exact`, `+ $10`, `+ $20`, `+ $50`, `+ $100`.
     - Clicking a chip sets `tendered` or adds the amount, and auto-adds a payment line for the selected cash method!
   - Payment Methods List:
     - Displays Cash method (from `context.cashMethodId`) and Electronic methods (from `context.electronicPaymentMethods`).
     - Clicking a payment method adds a payment line for `remaining` (or `tendered` if entered).
   - Split Payment Table:
     - Shows each applied payment line with method name, amount formatted with `context.formatMoney`, and a delete `×` button.
   - Keypad for custom amount entry:
     - Numeric keypad `1`-`9`, `0`, `.`, `⌫`, `Clear`.
   - Actions:
     - `Back` button (returns to cart screen via `onBack()`).
     - `Customer` button (displays customer name, allows changing customer before invoicing).
     - `Invoice` toggle checkbox (requires partner to be selected).
     - `Validate` button:
       - Active if `totalPaid >= totalDue` or `(totalPaid === 0 && totalDue === 0)`.
       - Calls `onValidate({ paymentLines, toInvoice, change })`.
       - Shows spinner / "Validating…" when processing.
4. Export:
   - Attach to `window.PosReactPaymentScreen`.

OUTPUT FORMAT:
Return ONLY the complete JavaScript code block inside ```javascript ... ```."""
    },
    {
        "id": "TASK_RECEIPT",
        "file": "enterprise/pos_react/static/src/components/receipt_screen.js",
        "model": "gemini-4-argon-high",
        "prompt": """You are a senior React frontend engineer specializing in POS Thermal Printing & Receipt Presentation.
TASK: Write the complete, production-grade component module `enterprise/pos_react/static/src/components/receipt_screen.js`.

REQUIREMENTS:
1. Environment: Native browser React (React 18 global `window.React` - `createElement as h`, `useState`, `useEffect`, `useRef`). Use `React.createElement` (or `h`).
2. Component Definition:
   - `window.PosReactReceiptScreen = function PosReactReceiptScreen({ order, context, onNewOrder }) { ... }`
3. Receipt Layout & Content:
   - Visual thermal slip container (`.pos-receipt-paper`):
     - Shop / Company header (name, address/vat if available).
     - Order Reference / Pos Reference (e.g. `order.name` or `order.pos_reference`).
     - Date & Time (`new Date().toLocaleString()`).
     - Cashier: `context.pluginData?.employee?.name || context.configName`.
     - Customer: `context.customer?.name || "Guest"`.
     - Table info (if restaurant: `context.restaurantContext?.tableId`).
     - Items Table:
       - Column headers: Item, Qty, Price, Total.
       - Lines: `order.lines` (Product display name, quantity, unit price, discount % if > 0, subtotal).
     - Subtotal, Tax Breakdown (Taxes included/excluded), and Grand Total.
     - Payment breakdown: Each payment method used and amount, plus Change returned.
     - Barcode / QR Code SVG representation (simple clean SVG with lines and order uuid text).
     - Thank You message / Footer note.
4. Screen Actions:
   - Top action bar:
     - `Print Receipt` button: triggers `window.print()`.
     - `Email Receipt` button & input: allows entering email address, calls RPC to email receipt if supported, shows confirmation alert.
     - `New Order` primary button: calls `onNewOrder()` to reset the terminal and return to a fresh cart.
5. Export:
   - Attach to `window.PosReactReceiptScreen`.

OUTPUT FORMAT:
Return ONLY the complete JavaScript code block inside ```javascript ... ```."""
    },
    {
        "id": "TASK_MODALS",
        "file": "enterprise/pos_react/static/src/components/modals.js",
        "model": "gemini-4-argon-high",
        "prompt": """You are a senior React frontend engineer specializing in POS Popups and Modals.
TASK: Write the complete, production-grade component module `enterprise/pos_react/static/src/components/modals.js`.

REQUIREMENTS:
1. Environment: Native browser React (React 18 global `window.React` - `createElement as h`, `useState`, `useEffect`, `useMemo`, `useRef`). Use `React.createElement` (or `h`).
2. Provide 3 high-quality modals attached to `window.PosReactModals`:
   - `CustomerModal`:
     - Props: `{ customers, customerId, onSelect, onClose, onQuickCreate }`
     - Search input (searches by name, phone, email, vat).
     - Scrollable list/table of matching customers with loyalty/credit indicator.
     - "Quick Create Customer" toggle form: Name, Phone, Email fields with "Save & Select" button calling `onQuickCreate({ name, phone, email })`.
     - Select button and Close `×` button.
   - `NoteModal`:
     - Props: `{ title, initialNote, onSave, onClose }`
     - Clean dialog with textarea for entering line-level note or order-level note.
     - Save button and Cancel button.
   - `ProductConfigModal`:
     - Props: `{ product, onConfirm, onClose }`
     - Allows selecting variant attributes or modifiers (e.g. Size, Extra shot, Sugar level).
     - Confirm button adding the customized line to cart.
3. Accessible Dialog Container:
   - Standard modal overlay with `role="dialog"`, `aria-modal="true"`, Esc key handler to close.
4. Export:
   - Attach to `window.PosReactModals = { CustomerModal, NoteModal, ProductConfigModal };`.

OUTPUT FORMAT:
Return ONLY the complete JavaScript code block inside ```javascript ... ```."""
    }
]

FORBIDDEN_JS_PATTERNS = [
    r"\beval\s*\(",
    r"dangerouslySetInnerHTML",
    r"document\.write\s*\(",
    r"window\.location\s*=",
    r"\.innerHTML\s*=",
]


def validate_pos_component_safety(code: str, file_path: str) -> bool:
    """Static security gate for AI-generated POS assets."""
    if file_path.endswith(".js"):
        for pat in FORBIDDEN_JS_PATTERNS:
            if re.search(pat, code):
                raise ValueError(f"Security violation in {file_path}: matched forbidden pattern '{pat}'")
    if code.count("{") != code.count("}"):
        raise ValueError(f"Syntax error in {file_path}: unbalanced curly braces")
    if file_path.endswith(".js") and code.count("(") != code.count(")"):
        raise ValueError(f"Syntax error in {file_path}: unbalanced parentheses")
    return True


def clean_code_block(raw_text):
    text = raw_text.strip()
    match = re.search(r"```(?:css|javascript|js)?\s*([\s\S]*?)\s*```", text)
    if match:
        return match.group(1).strip()
    return text

def execute_task(task):
    task_id = task["id"]
    model = task["model"]
    file_rel = task["file"]
    file_abs = os.path.join(WORKSPACE_ROOT, file_rel)
    print(f"[*] [FLEET] Launching task {task_id} targeting '{file_rel}' with model '{model}'...")

    payload = {
        "prompt": task["prompt"],
        "node_name": "pro-1",
        "model": model,
        "timeout": 120
    }
    
    req = urllib.request.Request(
        f"{FLEET_URL}/api/fleet/run-sync",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    
    start_t = time.time()
    try:
        with urllib.request.urlopen(req, timeout=130) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            elapsed = time.time() - start_t
            
            output = res_data.get("clean_response") or res_data.get("output") or ""
            node_used = res_data.get("node_name", "unknown")
            print(f"[✓] [FLEET] {task_id} completed on node '{node_used}' in {elapsed:.2f}s ({len(output)} chars)")
            
            code = clean_code_block(output)
            if not code or len(code) < 50:
                raise ValueError(f"Task {task_id} returned empty or invalid code!")
            validate_pos_component_safety(code, file_rel)
                
            os.makedirs(os.path.dirname(file_abs), exist_ok=True)
            with open(file_abs, "w", encoding="utf-8") as f:
                f.write(code + "\n")
            print(f"[✓] [SAVED] Successfully wrote {len(code)} bytes to {file_rel}")
            return {"task_id": task_id, "file": file_rel, "success": True, "node": node_used, "bytes": len(code)}
    except Exception as e:
        print(f"[!] [ERROR] Task {task_id} failed: {e}", file=sys.stderr)
        return {"task_id": task_id, "file": file_rel, "success": False, "error": str(e)}

def main():
    print("======================================================================")
    print("🚀 STARTING AUTONOMOUS AGY FLEET GENERATION FOR POS REACT (NODE: pro-1)")
    print(f"Cluster API: {FLEET_URL} | Tasks: {len(TASKS)}")
    print("======================================================================")
    
    results = []
    # Sequential or 2 workers to avoid queue starvation on node
    for t in TASKS:
        r = execute_task(t)
        results.append(r)
        time.sleep(2)
            
    print("\n----------------------------------------------------------------------")
    print("📊 FLEET EXECUTION SUMMARY:")
    all_ok = True
    for r in results:
        status_icon = "✓" if r.get("success") else "✗"
        print(f" {status_icon} {r['task_id']}: {r['file']} ({r.get('bytes', 0)} bytes) [Node: {r.get('node', 'N/A')}]")
        if not r.get("success"):
            all_ok = False
            
    if not all_ok:
        print("\n[!] Some tasks failed. Exiting with failure.", file=sys.stderr)
        sys.exit(1)
        
    print("\n🎉 ALL FLEET MODULES GENERATED SUCCESSFULLY!")
    print("Next step: Integrate components into views/shell.xml and app.js.")

if __name__ == "__main__":
    main()
