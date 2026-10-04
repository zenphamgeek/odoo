This is a deep technical brief. I'll give you concrete, implementable patterns for all three areas. Where I'm reasoning about Odoo/OWL internals from the framework's known structure rather than your actual repo, I'll flag it so you can verify against your fork.# 1. HOOT Harness & CEW 10-Gate Hardening
## Gate 7: Counter Code Scanner false positive
The core issue is that `$o-brand-odoo` is a semantically required SCSS token (Odoo's theme engine references `$o-brand-odoo` internally in `_bootstrap_overridden.scss` and button mixins). You can't delete it without breaking the cascade, but it trips a literal `odoo` substring scan. The fix is a scoped, auditable allowlist rather than a blanket skip.### `scripts/counter_code_scanner.py`
```python
"""
Counter Code Scanner — Gate 7
Scans for residual 'odoo' brand leaks in source.Supports an inline ignore directive for technically-required tokens.Ignore mechanism:
    - Append `// counter-scanner-ignore` on the SAME line to suppress one hit.    - The directive is logged to the audit report so suppressions stay visible.      This keeps 100% strictness: nothing is silently skipped, every
      suppression is counted and reported."""
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
IGNORE_DIRECTIVE = "counter-scanner-ignore"
# Case-insensitive brand token. \b avoids matching inside words like 'odoobot'
# when we WANT those treated separately (see Gate 10 asset handling).BRAND_PATTERN = re.compile(r"\bodoo\b", re.IGNORECASE)
# Comment leaders per file type so the directive works in scss/js/py/xml.COMMENT_LEADERS = ("//", "#", "<!--", "/*")
@dataclass
class ScanResult:
    violations: list = field(default_factory=list)   # (path, lineno, line)
    suppressions: list = field(default_factory=list) # (path, lineno, line)
    @property
    def failed(self) -> bool:
        return bool(self.violations)
def _has_ignore_directive(line: str) -> bool:
    # Directive must appear inside a comment segment on the same line.    for leader in COMMENT_LEADERS:
        idx = line.find(leader)
        if idx != -1 and IGNORE_DIRECTIVE in line[idx:]:
            return True
    return False
def scan_file(path: Path, result: ScanResult) -> None:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeError):
        return
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not BRAND_PATTERN.search(line):
            continue
        if _has_ignore_directive(line):
            result.suppressions.append((str(path), lineno, line.strip()))
        else:
            result.violations.append((str(path), lineno, line.strip()))
def scan_tree(root: Path, exts=(".scss", ".js", ".xml", ".py", ".css")) -> ScanResult:
    result = ScanResult()
    for path in root.rglob("*"):
        if path.suffix in exts and path.is_file():
            scan_file(path, result)
    return result
def report(result: ScanResult) -> int:
    if result.suppressions:
        print(f"[Gate 7] {len(result.suppressions)} audited suppression(s):")
        for p, n, line in result.suppressions:
            print(f"    IGNORED  {p}:{n}  {line}")
    if result.failed:
        print(f"\n[Gate 7] FAIL — {len(result.violations)} brand leak(s):")
        for p, n, line in result.violations:
            print(f"    LEAK     {p}:{n}  {line}")
        return 1
    print("\n[Gate 7] PASS — no un-suppressed brand leaks.")
    return 0
if __name__ == "__main__":
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    sys.exit(report(scan_tree(root)))
```
Two design choices worth noting. First, suppressions are counted and printed, not swallowed — a reviewer sees every `counter-scanner-ignore` in CI output, so strictness holds. Second, `\bodoo\b` with word boundaries means `odoobot.svg` won't match this rule; that's intentional and ties into Gate 10 below.### SCSS updates
In both `addons/web/static/src/scss/primary_variables.scss` and `enterprise/web_enterprise/static/src/scss/primary_variables.scss`:
```scss
// The $o-brand-odoo token is consumed by Bootstrap overrides and button
// mixins in the theme engine. It is a structural variable name, not a
// user-facing brand string. Aliased to the sovereign primary.$o-brand-insilos: #714B67 !default;                        // sovereign token
$o-brand-odoo: $o-brand-insilos !default; // counter-scanner-ignore
```
This gives you a forward-facing `$o-brand-insilos` token to migrate toward, while the legacy name stays wired up for the ~hundreds of internal references. The ignore comment is on the one line that legitimately must retain the string.## Gate 10: HOOT + Playwright — true leaks vs. compat mocks
The distinction you want is intent: a brand string in a user-visible DOM node or network payload is a leak; the same string as an asset filename or a backward-compat mock key is not. Encode that as explicit allowlists rather than loose regex.```javascript
// tests/gate10/brand_sweep.hoot.js
import { test, expect } from "@odoo/hoot"; // framework import stays as-is
import { mountWebClient } from "@insilos/hoot-helpers";
// Technical exceptions: asset filenames and compat identifiers that MUST
// retain the legacy token for cache/CDN/back-compat reasons.const TECHNICAL_ALLOWLIST = [
    /odoobot\.(svg|png)$/,          // avatar asset path (served, not shown as text)
    /\/web\/image\/.*odoobot/,       // image controller fallbacks
    /data-legacy-mock="odoo"/,       // explicit test mocks
];
function isTechnical(value) {
    return TECHNICAL_ALLOWLIST.some((re) => re.test(value));
}
test("no visible 'odoo' text in rendered web client", async () => {
    const el = await mountWebClient();
    // 1. Visible text content — strict, no allowlist. Text is always a leak.    const textNodes = [...el.querySelectorAll("*")]
        .flatMap((n) => [...n.childNodes])
        .filter((c) => c.nodeType === Node.TEXT_NODE)
        .map((c) => c.textContent.trim())
        .filter(Boolean);
    for (const text of textNodes) {
        expect(/\bodoo\b/i.test(text)).toBe(false,
            `Visible brand leak in text: "${text}"`);
    }
    // 2. Attributes — allow technical asset refs, flag everything else.    for (const node of el.querySelectorAll("*")) {
        for (const attr of node.attributes) {
            const v = attr.value;
            if (/odoo/i.test(v) && !isTechnical(v)) {
                expect.step(`LEAK attr ${attr.name}="${v}"`);
            }
        }
    }
    expect.verifySteps([]);
});
```
Playwright side, same split — assert on what a user actually sees:
```javascript
// e2e/gate10.spec.js
import { test, expect } from "@playwright/test";
test("brand sweep — visible surfaces only", async ({ page }) => {
    await page.goto("/web");
    await page.waitForLoadState("networkidle");
    // Visible innerText never contains the legacy brand.    const bodyText = await page.locator("body").innerText();
    expect(bodyText).not.toMatch(/\bodoo\b/i);
    // Bot greeting is rebranded.    await page.getByRole("button", { name: /messaging|discuss/i }).click();
    const greeting = await page.locator(".o-mail-Message-content").first().innerText();
    expect(greeting).toContain("InsilosBot");
    expect(greeting).not.toMatch(/odoobot/i); // display name, not asset
    // Network payloads carry sovereign headers.    const resp = await page.waitForResponse(/\/web\/dataset\/call_kw/);
    expect(resp.request().headers()["x-insilos-client"]).toBeTruthy();
});
```
The principle: text content and payload semantics get zero tolerance; asset paths and explicitly tagged mocks get a named, reviewable allowlist.# 2. Hard Refactor at Code Signature Level
The constraint that governs everything here: 700+ addons reference `odoo.define`-era globals, `o_`/`o-mail-` CSS classes, and `window.odoo` in QWeb `t-on`/`t-att` expressions. You cannot rename these in place without a flag-day migration. The sovereign strategy is additive aliasing — new canonical names that forward to the old ones, with the old names deprecated but functional.## `window.odoo` → `window.insilos` bridge
Install the alias as early as possible in the boot sequence, before any module reads the global.```javascript
// addons/web/static/src/legacy/insilos_global_bridge.js
// Loaded first in the web.assets_backend bundle (prepend in manifest).(function bridgeGlobal() {
    const root = globalThis;
    if (!root.odoo) {
        // If the fork ever boots insilos-first, mirror back for compat.        return;
    }
    // Live alias: insilos IS odoo (same reference), so late mutations on
    // either (define, loader, __session_info__) stay in sync.    if (!root.insilos) {
        Object.defineProperty(root, "insilos", {
            get: () => root.odoo,
            set: (v) => { root.odoo = v; },
            configurable: true,
            enumerable: false,
        });
    }
})();
```
A getter/setter alias (not a shallow copy) is critical here — Odoo mutates `odoo.loader`, `odoo.define`, and `odoo.__session_info__` throughout boot. A copy would desync. New Insilos-native modules import from `@insilos/*` and read `window.insilos`; legacy addons keep working untouched.## CSS class strategy — scoped theme, not rename
Renaming `o_` / `o-mail-` classes breaks every XML template that targets them. Instead, treat the `o_` prefix as a structural namespace (like a vendor prefix) and own the *appearance* through a theme layer and CSS custom properties. This is the lowest-risk path by far.```scss
// addons/web/static/src/scss/insilos_theme.scss
// We don't rename .o_* classes. We re-skin them via custom properties
// so 700+ templates keep their selectors but render sovereign styling.:root {
    --insilos-focus-ring: #0f62fe;      // light
    --insilos-brand: #714B67;
}
.o-dark, [data-theme="dark"] {
    --insilos-focus-ring: #00F2FE;      // dark
}
// Unified composer capsule focus ring — one source of truth..o-mail-Composer:focus-within,
.o-mail-Composer-input:focus {
    outline: none;
    box-shadow: 0 0 0 2px var(--insilos-focus-ring);
    border-radius: 12px; // capsule
}
```
If you later want human-facing sovereign class names for *new* components, add them as additional classes rather than replacements: `class="o_form_view insilos-form"`. Both resolve; nothing breaks.## Registry descriptors
Registries are keyed by string. Don't rename categories — wrap the API so new code uses sovereign naming while entries land in the same underlying category.```javascript
// addons/web/static/src/core/insilos_registry.js
import { registry } from "@web/core/registry";
// Sovereign facade. `registry.category("actions")` and
// insilosRegistry.category("actions") return the SAME store.export const insilosRegistry = {
    category: (name) => registry.category(name),
    addMeta: (name, key, value) => registry.category(name).add(key, {
        ...value,
        __insilos: { brandedAt: Date.now() },
    }),
};
```
The payoff is you can add provenance metadata (`__insilos`) without touching category keys that actions, fields, and services resolve against.## RPC headers and payload branding
Headers are the clean place to assert sovereign identity — they're invisible to QWeb and don't collide with Odoo's JSON-RPC envelope schema (which you should *not* rename; the server expects `jsonrpc`, `method`, `params`).```javascript
// addons/web/static/src/core/network/insilos_rpc_patch.js
import { rpcBus } from "@web/core/network/rpc";
import { browser } from "@web/core/browser/browser";
// Patch the fetch used by the rpc service to brand transport-layer only.const _fetch = browser.fetch;
browser.fetch = (url, opts = {}) => {
    if (typeof url === "string" && url.startsWith("/web/dataset")) {
        opts.headers = {
            ...(opts.headers || {}),
            "X-Insilos-Client": "web/20.0",
            "X-Insilos-Session": "insilos_session_id",
        };
    }
    return _fetch(url, opts);
};
```
Keep the JSON-RPC body untouched. Brand the envelope (headers), never the protocol fields — that's the line between sovereign identity and a broken client.### Migration sequencing
1. Land the global bridge + theme layer + header patch. Zero behavioral change, fully reversible.2. Point new/rebuilt modules at `@insilos/*` imports and `window.insilos`.3. Add a lint rule flagging *new* `o_`-prefixed classes in Insilos-native modules (legacy stays exempt).4. Deprecate — never delete — legacy aliases on a long horizon once addon audit shows no consumers.# 3. UI Performance at Scale
## CSS Containment
The big wins are List rows, Kanban columns, and KPI cards because they're the high-cardinality repeated nodes. `content-visibility: auto` skips rendering off-screen subtrees entirely; `contain-intrinsic-size` prevents scroll-jump by reserving space.```scss
// addons/web/static/src/scss/insilos_perf_containment.scss
// List rows: isolate layout/paint, skip offscreen render work..o_list_table tbody > tr {
    content-visibility: auto;
    contain-intrinsic-size: auto 40px;  // tune to your avg row height
    contain: layout paint style;
}
// Kanban columns: each column is an independent containment root..o_kanban_group {
    contain: content;                   // layout + paint + style + size
    content-visibility: auto;
    contain-intrinsic-size: auto 600px;
}
// Dashboard KPI cards..o_dashboard .o_kpi_card {
    contain: content;
    content-visibility: auto;
    contain-intrinsic-size: 240px 160px;
}
```
One caveat worth verifying in your fork: `content-visibility: auto` on list rows can interfere with sticky headers and keyboard navigation to off-screen rows. Test tab-order and `scrollIntoView` on hidden rows. If nav breaks, drop `content-visibility` on rows and keep just `contain: layout paint`.## OWL 2 reactivity — kill redundant re-renders
Three patterns cover most of the waste.Subscribe narrowly. Reading a whole store object in render subscribes the component to every key on it. Destructure the slice you need:
```javascript
// Bad — re-renders on ANY store change.setup() {
    this.store = useState(useService("mail.store"));
}
// Good — only tracks the threads slice.setup() {
    const store = useService("mail.store");
    this.state = useState({ get threads() { return store.threads; } });
}
```
Memoize derived values so you don't recompute heavy lists each render:
```javascript
import { useState } from "@odoo/owl";
function useMemoized(getDeps, compute) {
    let lastDeps, lastVal;
    return () => {
        const deps = getDeps();
        if (!lastDeps || deps.some((d, i) => d !== lastDeps[i])) {
            lastDeps = deps;
            lastVal = compute(...deps);
        }
        return lastVal;
    };
}
// Usage in setup():
this.sortedRecords = useMemoized(
    () => [this.props.records, this.props.sortKey],
    (records, key) => [...records].sort((a, b) => a[key] - b[key]),
);
```
Use `t-key` on list iterations so OWL patches instead of recreating DOM, and split large components so a KPI tick doesn't re-render the whole dashboard:
```xml
<t t-foreach="records" t-as="rec" t-key="rec.id">
    <RecordRow record="rec"/>  <!-- isolated; only changed rows re-render -->
</t>
```
## Asset bundle code splitting
`web_studio`, `web_gantt`, `web_map`, `web_cohort` are heavy and rarely all needed at once. Pull them out of the main backend bundle into lazy bundles loaded on demand.```python
# web_gantt/__manifest__.py — define a separate, non-eager bundle.{
    "assets": {
        # NOT in web.assets_backend — loaded only when a gantt view opens.        "web_gantt.assets_lazy": [
            "web_gantt/static/src/**/*.js",
            "web_gantt/static/src/**/*.scss",
            "web_gantt/static/src/**/*.xml",
        ],
    },
}
```
```javascript
// Lazy-load the view bundle the first time the gantt view type is requested.import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
const viewRegistry = registry.category("views");
registry.category("lazy_views").add("gantt", async () => {
    await loadBundle("web_gantt.assets_lazy");
    return viewRegistry.get("gantt");
});
```
Measure first: run `odoo --dev=assets` and inspect bundle sizes. Studio in particular can be 30%+ of the backend bundle for users who never open it.## Network / RPC batching + metadata cache
Batch `read` calls fired in the same tick (common when a kanban renders many records), and cache immutable metadata (`fields_get`, actions, views) which almost never changes within a session.```javascript
// addons/web/static/src/core/network/insilos_rpc_batch.js
import { rpc } from "@web/core/network/rpc";
class ReadBatcher {
    constructor() { this.queue = new Map(); this.scheduled = false; }
    read(model, ids, fields) {
        return new Promise((resolve) => {
            const key = `${model}:${fields.sort().join(",")}`;
            if (!this.queue.has(key)) this.queue.set(key, { model, fields, items: [] });
            this.queue.get(key).items.push({ ids, resolve });
            if (!this.scheduled) {
                this.scheduled = true;
                queueMicrotask(() => this.flush());
            }
        });
    }
    async flush() {
        const batches = [...this.queue.values()];
        this.queue.clear();
        this.scheduled = false;
        for (const { model, fields, items } of batches) {
            const allIds = [...new Set(items.flatMap((i) => i.ids))];
            const records = await rpc("/web/dataset/call_kw", {
                model, method: "read", args: [allIds, fields], kwargs: {},
            });
            const byId = new Map(records.map((r) => [r.id, r]));
            for (const it of items) {
                it.resolve(it.ids.map((id) => byId.get(id)).filter(Boolean));
            }
        }
    }
}
export const readBatcher = new ReadBatcher();
```
```javascript
// Session-scoped metadata cache for immutable descriptors.const metaCache = new Map();
export async function cachedFieldsGet(model) {
    if (metaCache.has(model)) return metaCache.get(model);
    const p = rpc("/web/dataset/call_kw", {
        model, method: "fields_get", args: [], kwargs: {},
    });
    metaCache.set(model, p);  // cache the promise to dedupe concurrent calls
    return p;
}
```
Caching the promise (not the resolved value) dedupes concurrent in-flight requests — a common source of duplicate `fields_get` on cold load. Invalidate `metaCache` on module upgrade events if your fork hot-reloads schemas.---
## Implementation plan / sequencing
Phase 1 — safe, reversible, land immediately: Gate 7 scanner + SCSS aliases, Gate 10 test splits, global bridge, theme/custom-property layer, RPC header branding, CSS containment. None of these change behavior or risk the 700-addon surface.Phase 2 — measured perf: profile bundle sizes, then code-split Studio/Gantt/Map/Cohort; add the read batcher and metadata cache; audit OWL store subscriptions in the hottest views (list, kanban, discuss).Phase 3 — long-horizon sovereignty: new modules adopt `@insilos/*` imports and sovereign classes additively; lint flags new legacy-prefixed names; deprecate aliases only after an audit proves zero consumers.A few things I'd want to verify against your actual fork before treating them as settled: the exact boot order of `web.assets_backend` (for where the global bridge must be prepended), whether your Discuss composer markup still uses `.o-mail-Composer` in Odoo 20 (class names drift between versions), and the real asset weight of each heavy module so the splitting effort targets the biggest wins. Want me to dig into any of those in the repo?