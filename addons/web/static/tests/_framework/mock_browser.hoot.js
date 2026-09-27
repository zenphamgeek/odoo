// ! WARNING: this module cannot depend on modules not ending with ".hoot" (except libs) !

import { mockLocation } from "@odoo/hoot";

//-----------------------------------------------------------------------------
// Exports
//-----------------------------------------------------------------------------

/**
 * Browser module needs to be mocked to patch the `location` global object since
 * it can't be directly mocked on the window object.
 *
 * @param {string} name
 * @param {OdooModuleFactory} factory
 */
export function mockBrowserFactory(name, { fn }) {
    return function mockBrowser(...args) {
        const browserModule = fn(...args);
        browserModule.location = mockLocation;
        browserModule.browser = new Proxy(browserModule.browser || window, {
            get(target, prop) {
                if (prop === "location") {
                    return mockLocation;
                }
                const value = target[prop];
                if (typeof value === "function") {
                    return value.bind(target);
                }
                return value;
            },
            set(target, prop, value) {
                if (prop === "location") {
                    if (typeof value === "string") {
                        mockLocation.href = value;
                    } else {
                        browserModule.location = value;
                    }
                    return true;
                }
                target[prop] = value;
                return true;
            },
        });
        return browserModule;
    };
}
