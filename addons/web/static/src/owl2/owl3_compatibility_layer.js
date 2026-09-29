/**
 * Owl 2 → Owl 3 compatibility layer.
 *
 * This file patches Owl 3 so that existing Owl 2 code can continue to run
 * with minimal changes. It is intended as a temporary bridge to ease
 * incremental migration from Owl 2 to Owl 3.
 *
 * ---------------------------------------------------------------------------
 * Setup (required to run Owl 2 code on Owl 3)
 * ---------------------------------------------------------------------------
 *
 * 1. Update template directives:
 *    - replace `t-portal` → `t-custom-portal`
 *    - replace `t-model`  → `t-custom-model`
 *
 * 2. Load this file immediately after Owl 3.
 *
 * 3. Update hooks:
 *    - replace all `useEffect` with `useLayoutEffect`
 *      import { useLayoutEffect } from "@insilos/owl";
 *
 * ---------------------------------------------------------------------------
 * Migration (once the app builds successfully)
 * ---------------------------------------------------------------------------
 *
 * Gradually remove the compatibility layer by migrating to native Owl 3:
 *
 * - replace `t-custom-portal` with proper Owl 3 portal usage
 * - replace `t-custom-model` with `t-model` + signals
 * - convert `useLayoutEffect` back to `useEffect` where appropriate
 *
 * The end goal is to eliminate all compatibility shims.
 */

// @ts-ignore
const owl = globalThis.owl;

class Component extends owl.Component {
    static get props() {
        return [];
    }
    static set props(value) {
        Object.defineProperty(this, "props", { value, writable: true, configurable: true });
    }

    /**
     * @param {any} node
     */
    constructor(node) {
        super(node);
        this.props = owl.useProps();
        if (this.constructor.defaultProps) {
            for (const [key, val] of Object.entries(this.constructor.defaultProps)) {
                if (this.props && this.props[key] === undefined) {
                    try {
                        this.props[key] = val;
                    } catch {}
                }
            }
        }
        this.env = useEnv();
    }

    /**
     * @param {boolean} [deep]
     */
    render(deep = false) {
        this.__owl__.render(deep === true);
    }
}
owl.Component = Component;
Object.defineProperty(owl.Component, "props", {
    get() {
        return [];
    },
    set(value) {
        Object.defineProperty(this, "props", { value, writable: true, configurable: true });
    },
    configurable: true,
});
function safeReactive(target, callback) {
    if (!target || typeof target !== "object") {
        return target;
    }
    try {
        return owl.proxy(target);
    } catch {
        return target;
    }
}
owl.reactive = safeReactive;
owl.useState = safeReactive;

/**
 * Owl 2 useRef hook compatibility shim.
 * @param {string} name
 */
function useRef(name) {
    const node = owl.useScope();
    const comp = node.component;
    if (comp) {
        if (comp[name + "Ref"] && typeof comp[name + "Ref"] === "function") {
            return comp[name + "Ref"];
        }
        if (comp[name] && typeof comp[name] === "function") {
            return comp[name];
        }
    }
    if (!node.__owl_refs__) {
        node.__owl_refs__ = {};
    }
    if (!node.__owl_refs__[name]) {
        node.__owl_refs__[name] = owl.signal.ref();
    }
    const signalRef = node.__owl_refs__[name];
    if (comp) {
        if (!comp[name]) {
            comp[name] = signalRef;
        }
        if (!comp[name + "Ref"]) {
            comp[name + "Ref"] = signalRef;
        }
    }
    if (!Object.prototype.hasOwnProperty.call(signalRef, "el")) {
        Object.defineProperty(signalRef, "el", {
            get() {
                return owl.untrack ? owl.untrack(() => signalRef()) : signalRef();
            },
            configurable: true,
        });
        Object.defineProperty(signalRef, "comp", {
            get() {
                return null;
            },
            configurable: true,
        });
    }
    return signalRef;
}
owl.useRef = useRef;
owl.useChildRef = useRef;

if (owl.signal && owl.signal.ref) {
    const origSignalRef = owl.signal.ref;
    owl.signal.ref = function (...args) {
        const s = origSignalRef.apply(this, args);
        if (s && !Object.prototype.hasOwnProperty.call(s, "el")) {
            Object.defineProperty(s, "el", {
                get() {
                    return owl.untrack ? owl.untrack(() => s()) : s();
                },
                configurable: true,
            });
            Object.defineProperty(s, "comp", {
                get() {
                    return null;
                },
                configurable: true,
            });
        }
        return s;
    };
}

/**
 * @param {() => void} cb
 */
owl.onWillRender = function onWillRender(cb) {
    const node = owl.useScope();
    const renderFn = node.renderFn;
    node.renderFn = () => {
        cb.call(node.component);
        return renderFn();
    };
};

/** kept for spreadsheet */
owl.useComponent = function useComponent() {
    return owl.useScope().component;
};

/**
 * @param {HTMLElement} target
 * @param {string} eventName
 * @param {Function} handler
 * @param {any} eventParams
 */
function useExternalListener(target, eventName, handler, eventParams) {
    const node = owl.useScope();
    const boundHandler = handler.bind(node.component);
    owl.onMounted(() => target.addEventListener(eventName, boundHandler, eventParams));
    owl.onWillUnmount(() => target.removeEventListener(eventName, boundHandler, eventParams));
}
owl.useExternalListener = useExternalListener; // kept for spreadsheet

/**
 * @param {Function} effect
 * @param {() => any[]} computeDependencies
 */
owl.useLayoutEffect = function useLayoutEffect(effect, computeDependencies = () => [NaN]) {
    /** @type {Function} */
    let cleanup;
    /** @type {any[]} */
    let dependencies;
    owl.onMounted(() => {
        dependencies = computeDependencies();
        cleanup = effect(...dependencies);
    });
    owl.onPatched(() => {
        const newDeps = computeDependencies();
        const shouldReapply = newDeps.some((val, i) => val !== dependencies[i]);
        if (shouldReapply) {
            dependencies = newDeps;
            if (cleanup) {
                cleanup();
            }
            cleanup = effect(...dependencies);
        }
    });
    owl.onWillUnmount(() => cleanup && cleanup());
};

const nativeUseEffect = owl.useEffect;
/**
 * @param {Function} effect
 * @param {() => any[]} [computeDependencies]
 */
owl.useEffect = function useEffect(effect, computeDependencies) {
    if (typeof computeDependencies === "function") {
        /** @type {Function} */
        let cleanup;
        /** @type {any[]} */
        let dependencies;
        owl.onMounted(() => {
            dependencies = computeDependencies();
            cleanup = effect(...dependencies);
        });
        owl.onPatched(() => {
            const newDeps = computeDependencies();
            const shouldReapply = !dependencies || newDeps.some((val, i) => val !== dependencies[i]);
            if (shouldReapply) {
                dependencies = newDeps;
                if (cleanup && typeof cleanup === "function") {
                    cleanup();
                }
                cleanup = effect(...dependencies);
            }
        });
        owl.onWillUnmount(() => cleanup && typeof cleanup === "function" && cleanup());
        return;
    }
    return nativeUseEffect(effect);
};

class EnvPlugin extends owl.Plugin {
    static id = "__ENV__";
    static sequence = 0;
    env = owl.useConfig("env");
}

function useEnv() {
    return owl.usePlugin(EnvPlugin).env;
}
owl.useEnv = useEnv;

/**
 * @param {object} extension
 */
function useSubEnv(extension) {
    const env = Object.create(useEnv());
    const descrs = Object.getOwnPropertyDescriptors(extension);
    const subEnv = Object.freeze(Object.defineProperties(env, descrs));
    owl.providePlugins([EnvPlugin], { env: subEnv });

    const component = owl.useScope().component;
    component.env = subEnv;
}
owl.useSubEnv = useSubEnv;
owl.useChildSubEnv = useSubEnv; // kept for spreadsheet

class VPortal extends owl.blockDom.text("").constructor {
    /**
     * @param {any} selector
     * @param {any} content
     */
    constructor(selector, content) {
        super("");
        this.content = content;
        this.selector = selector;
        this.target = null;
    }

    /**
     * @param {any} parent
     * @param {any} anchor
     */
    mount(parent, anchor) {
        super.mount(parent, anchor);
        this.target = document.querySelector(this.selector);
        if (this.target) {
            this.content.mount(this.target, null);
        } else {
            this.content.mount(parent, anchor);
        }
    }

    beforeRemove() {
        this.content.beforeRemove();
    }

    remove() {
        if (this.content) {
            super.remove();
            this.content.remove();
            this.content = null;
        }
    }

    /**
     * @param {any} other
     */
    patch(other) {
        super.patch(other);
        if (this.content) {
            this.content.patch(other.content, true);
        } else {
            this.content = other.content;
            this.content.mount(this.target, null);
        }
    }
}

class Portal extends owl.Component {
    static template = owl.xml`<t t-call-slot="default"/>`;

    setup() {
        const node = this.__owl__;
        const renderContent = node.renderFn;
        node.renderFn = (/** @type {any[]} */ ...args) =>
            new VPortal(node.props.selector, renderContent(...args));

        owl.onMounted(() => {
            const portal = node.bdom;
            if (!portal.target) {
                const target = portal.el.ownerDocument.querySelector(node.props.selector);
                if (target) {
                    portal.content.moveBeforeDOMNode(target.firstChild, target);
                } else {
                    throw new Error("invalid portal target");
                }
            }
        });

        owl.onWillUnmount(() => {
            const portal = node.bdom;
            portal.remove();
        });
    }
}

const customDirectives = {
    /**
     * @param {HTMLElement} node
     * @param {string} value
     */
    model: (node, value) => {
        // kept for spreadsheet
        node.setAttribute("t-model.proxy", value);
    },
    /**
     * @param {HTMLElement} node
     * @param {string} value
     */
    portal: (node, value) => {
        if (node.nodeName.toLowerCase() !== "t") {
            throw new Error("t-custom-portal should be on a 't' element");
        }
        node.setAttribute("t-component", "__globals__.Portal");
        node.setAttribute("selector", value);
    },
};

const globalValues = {
    Portal,
};

class App extends owl.App {
    /**
     * @param {any} config
     */
    constructor(config) {
        const env = config.env ?? {};
        if (config.plugins) {
            if (config.plugins instanceof owl.Resource) {
                config.plugins.add(EnvPlugin);
            } else {
                config.plugins.push(EnvPlugin);
            }
        } else {
            config.plugins = [EnvPlugin];
        }
        super({
            ...config,
            customDirectives: {
                ...customDirectives,
                ...config.customDirectives,
            },
            globalValues: {
                ...globalValues,
                ...config.globalValues,
            },
            config: config.config ? Object.assign(Object.create(config.config), { env }) : { env },
        });
        this.env = env;

        if (this.runtimeUtils && this.runtimeUtils.createRef) {
            const origCreateRef = this.runtimeUtils.createRef;
            this.runtimeUtils.createRef = function (ref, node) {
                if (!ref) {
                    return () => {};
                }
                return origCreateRef(ref, node);
            };
        }
    }

    getTemplate(name) {
        let template;
        try {
            template = super.getTemplate(name);
        } catch (e) {
            try {
                const emptyDoc = new DOMParser().parseFromString("<t/>", "text/xml").documentElement;
                this.addTemplate(name, emptyDoc);
                template = super.getTemplate(name);
            } catch {
                throw e;
            }
        }
        if (!template.__owl_compat_wrapped__) {
            const wrapped = function (ctx, node, key = "") {
                if (ctx && !ctx.__is_owl_compat_proxy__ && ctx.__owl__) {
                    const componentNode = ctx.__owl__;
                    ctx = new Proxy(ctx, {
                        get(target, prop, receiver) {
                            if (prop === "__is_owl_compat_proxy__") {
                                return true;
                            }
                            if (prop === "then") {
                                return undefined;
                            }
                            if (prop in target) {
                                return Reflect.get(target, prop, receiver);
                            }
                            if (componentNode.__owl_refs__ && prop in componentNode.__owl_refs__) {
                                return componentNode.__owl_refs__[prop];
                            }
                            const comp = target.this;
                            if (comp && typeof prop === "string" && prop in comp) {
                                const val = comp[prop];
                                if (typeof val === "function") {
                                    if (Object.getOwnPropertySymbols(val).length > 0 || typeof val.set === "function") {
                                        return val;
                                    }
                                    return val.bind(comp);
                                }
                                return val;
                            }
                            return Reflect.get(target, prop, receiver);
                        },
                    });
                }
                return template.call(this, ctx, node, key);
            };
            wrapped.__owl_compat_wrapped__ = true;
            this.templates[name] = wrapped;
            return wrapped;
        }
        return template;
    }

    createRoot(component, config = {}) {
        if (config.env) {
            component = {
                [component.name]: class extends component {
                    constructor(node) {
                        owl.providePlugins([EnvPlugin], { env: config.env });
                        super(node);
                    }
                },
            }[component.name];
        }
        return super.createRoot(component, config);
    }
}
owl.App = App;

/**
 * @param {any} C
 * @param {any} target
 * @param {any} config
 */
async function mount(C, target, config = {}) {
    return new App(config).createRoot(C, config).mount(target, config);
}
owl.mount = mount;

owl.__ODOO_COMPATIBILITY_LAYER_ADDED__ = true;
