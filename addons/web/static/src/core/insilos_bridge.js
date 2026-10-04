/** @odoo-module **/
/**
 * ============================================================================
 * INSILOS SOVEREIGN CLIENT-SIDE VIRTUALIZATION BRIDGE
 * Bidirectional Window & Module Registry Virtualizer (OWL 3 / WebClient)
 * ============================================================================
 * Establishes window.insilos as the sovereign runtime namespace while maintaining
 * 100% transparent proxying to and from window.odoo.
 */

(function () {
    "use strict";

    // 1. Establish window.insilos Sovereign Object
    if (!window.insilos) {
        window.insilos = {};
    }

    // Platform metadata
    window.insilos.brand = "Insilos Enterprise Platform";
    window.insilos.version = "20.0";
    window.insilos.edition = "Sovereign Enterprise";

    // 2. Dual-Registry Virtualization
    if (window.odoo) {
        // Link define and loader
        if (window.odoo.define && !window.insilos.define) {
            window.insilos.define = function () {
                return window.odoo.define.apply(window.odoo, arguments);
            };
        }
        if (window.odoo.loader && !window.insilos.loader) {
            window.insilos.loader = window.odoo.loader;
        }
    }

    // 3. Bidirectional Proxy for Dynamic Properties
    try {
        const odooHandler = {
            get(target, prop, receiver) {
                if (prop in target) {
                    return Reflect.get(target, prop, receiver);
                }
                if (window.odoo && prop in window.odoo) {
                    const val = window.odoo[prop];
                    return typeof val === "function" ? val.bind(window.odoo) : val;
                }
                return undefined;
            },
            set(target, prop, value, receiver) {
                if (window.odoo) {
                    window.odoo[prop] = value;
                }
                return Reflect.set(target, prop, value, receiver);
            },
        };
        window.insilos = new Proxy(window.insilos, odooHandler);
    } catch (_e) {
        // Fallback for environments where Proxy on window properties is constrained
        Object.assign(window.insilos, window.odoo || {});
    }

    // 4. Session Identification & Dual-Cookie Synchronization
    function getCookie(name) {
        const matches = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, "\\$1") + "=([^;]*)"));
        return matches ? decodeURIComponent(matches[1]) : undefined;
    }

    window.insilos.getSessionId = function () {
        return getCookie("insilos_session_id") || getCookie("session_id");
    };

    // 5. Console Greeting
    if (typeof console !== "undefined" && console.info) {
        console.info(
            "%c[INSILOS ENTERPRISE]%c Sovereign Web Client v20.0 initialized (Zero Genesis Footprint)",
            "background: #0B2E64; color: #00F0FF; font-weight: bold; padding: 2px 6px; border-radius: 2px;",
            "color: #10B981; font-weight: 500;"
        );
    }
})();

export const insilosBridge = window.insilos;
export default insilosBridge;
