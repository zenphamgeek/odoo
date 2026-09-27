path = "/home/zen/O20/enterprise/insilos_website/static/src/js/c3ai_interactive.js"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

observer_code = """
            // Setup MutationObserver for Snippet Options dynamically updating content
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === "attributes" && mutation.attributeName.startsWith("data-l")) {
                        const attr = mutation.attributeName; // e.g. data-l1-title
                        const match = attr.match(/^data-l(\\d)-(.*)$/);
                        if (match) {
                            const layerNum = match[1];
                            const field = match[2];
                            const val = vp.getAttribute(attr);
                            const card = vp.querySelector(`.ins-cockpit-card[data-layer="${layerNum}"]`);
                            if (card && val !== null) {
                                if (field === 'title') {
                                    const el = card.querySelector('.ins-cockpit-title');
                                    if (el) el.innerText = val;
                                } else if (field === 'icon') {
                                    const el = card.querySelector('use');
                                    if (el) el.setAttribute('href', `/insilos_website/static/src/icons/phosphor-duotone.svg#ph-${val}`);
                                } else if (field === 'badge') {
                                    const el = card.querySelector('.ins-cockpit-badge');
                                    if (el) el.innerText = val;
                                } else if (field === 'metric') {
                                    const el = card.querySelector('.fw-medium.font-monospace.small');
                                    if (el) el.innerText = val;
                                } else if (field === 'desc') {
                                    const el = card.querySelector('.d-flex.justify-content-between.text-secondary.small span:first-child');
                                    if (el) el.innerText = val;
                                }
                            }
                        }
                    }
                });
            });
            observer.observe(vp, { attributes: true });
"""

# Insert right after `vp.__cockpit_initialized = true;`
target = "vp.__cockpit_initialized = true;"
content = content.replace(target, target + observer_code)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)
