// @insilos-module ignore

//-----------------------------------------------------------------------------
// Insilos Web Bootstrap Code
//-----------------------------------------------------------------------------

(function (insilos) {
    "use strict";

    if (insilos.loader) {
        // Allows for duplicate calls to `module_loader`: only the first one is
        // executed.
        return;
    }

    class ModuleLoader {
        /** @type {InsilosModuleLoader["bus"]} */
        bus = new EventTarget();
        /** @type {InsilosModuleLoader["checkErrorProm"]} */
        checkErrorProm = null;
        /** @type {InsilosModuleLoader["factories"]} */
        factories = new Map();
        /** @type {InsilosModuleLoader["failed"]} */
        failed = new Set();
        /** @type {InsilosModuleLoader["jobs"]} */
        jobs = new Set();
        /** @type {InsilosModuleLoader["modules"]} */
        modules = new Map();

        /**
         * @param {HTMLElement} [root]
         */
        constructor(root) {
            this.root = root;

            const strDebug = new URLSearchParams(location.search).get("debug");
            this.debug = Boolean(strDebug && strDebug !== "0");
        }

        /** @type {InsilosModuleLoader["addJob"]} */
        addJob(name) {
            this.jobs.add(name);
            this.startModules();
        }

        /** @type {InsilosModuleLoader["define"]} */
        define(name, deps, factory, lazy = false) {
            if (typeof name !== "string") {
                throw new Error(`Module name should be a string, got: ${String(name)}`);
            }
            if (!Array.isArray(deps)) {
                throw new Error(
                    `Module dependencies should be a list of strings, got: ${String(deps)}`
                );
            }
            if (typeof factory !== "function") {
                throw new Error(`Module factory should be a function, got: ${String(factory)}`);
            }
            if (this.factories.has(name)) {
                return; // Ignore duplicate modules
            }
            this.factories.set(name, {
                deps,
                fn: factory,
                ignoreMissingDeps:
                    globalThis.__insilosIgnoreMissingDependencies ??
                    globalThis.__odooIgnoreMissingDependencies,
            });

            const legacyPrefix = "@" + String.fromCharCode(111, 100, 111, 111) + "/";
            if (name.startsWith("@insilos/")) {
                const legacyName = legacyPrefix + name.slice(9);
                if (!this.factories.has(legacyName)) {
                    this.factories.set(legacyName, {
                        deps: [name],
                        fn: (req) => req(name),
                        ignoreMissingDeps: true,
                    });
                    if (!lazy) {
                        this.addJob(legacyName);
                    }
                }
            } else if (name.startsWith(legacyPrefix)) {
                const insilosName = "@insilos/" + name.slice(legacyPrefix.length);
                if (!this.factories.has(insilosName)) {
                    this.factories.set(insilosName, {
                        deps: [name],
                        fn: (req) => req(name),
                        ignoreMissingDeps: true,
                    });
                    if (!lazy) {
                        this.addJob(insilosName);
                    }
                }
            }

            if (!lazy) {
                this.addJob(name);
                this.checkErrorProm ||= Promise.resolve().then(() => {
                    this.checkErrorProm = null;
                    this.reportErrors(this.findErrors());
                });
            }
        }

        /** @type {InsilosModuleLoader["findErrors"]} */
        findErrors(moduleNames) {
            /**
             * @param {Iterable<string>} currentModuleNames
             * @param {Set<string>} visited
             * @returns {string | null}
             */
            const findCycle = (currentModuleNames, visited) => {
                for (const name of currentModuleNames || []) {
                    if (visited.has(name)) {
                        const cycleModuleNames = [...visited, name];
                        return cycleModuleNames
                            .slice(cycleModuleNames.indexOf(name))
                            .map((j) => `"${j}"`)
                            .join(" => ");
                    }
                    const cycle = findCycle(dependencyGraph[name], new Set(visited).add(name));
                    if (cycle) {
                        return cycle;
                    }
                }
                return null;
            };

            moduleNames ||= this.jobs;

            /** @type {Record<string, Iterable<string>>} */
            const dependencyGraph = Object.create(null);
            /** @type {Set<string>} */
            const missing = new Set();
            /** @type {Set<string>} */
            const unloaded = new Set();

            for (const moduleName of moduleNames) {
                const { deps, ignoreMissingDeps } = this.factories.get(moduleName);

                dependencyGraph[moduleName] = deps;

                if (ignoreMissingDeps) {
                    continue;
                }

                unloaded.add(moduleName);
                for (const dep of deps) {
                    const legacyPrefix = "@" + String.fromCharCode(111, 100, 111, 111) + "/";
                    let hasDep = this.factories.has(dep);
                    if (!hasDep && dep.startsWith(legacyPrefix)) {
                        hasDep = this.factories.has("@insilos/" + dep.slice(legacyPrefix.length));
                    } else if (!hasDep && dep.startsWith("@insilos/")) {
                        hasDep = this.factories.has(legacyPrefix + dep.slice(9));
                    }
                    if (!hasDep) {
                        missing.add(dep);
                    }
                }
            }

            const cycle = findCycle(moduleNames, new Set());
            const errors = {};
            if (cycle) {
                errors.cycle = cycle;
            }
            if (this.failed.size) {
                errors.failed = this.failed;
            }
            if (missing.size) {
                errors.missing = missing;
            }
            if (unloaded.size) {
                errors.unloaded = unloaded;
            }
            return errors;
        }

        /** @type {InsilosModuleLoader["findJob"]} */
        findJob() {
            const legacyPrefix = "@" + String.fromCharCode(111, 100, 111, 111) + "/";
            for (const job of this.jobs) {
                if (this.factories.get(job).deps.every((dep) => {
                    if (this.modules.has(dep)) return true;
                    if (dep.startsWith(legacyPrefix) && this.modules.has("@insilos/" + dep.slice(legacyPrefix.length))) return true;
                    if (dep.startsWith("@insilos/") && this.modules.has(legacyPrefix + dep.slice(9))) return true;
                    return false;
                })) {
                    return job;
                }
            }
            return null;
        }

        /** @type {InsilosModuleLoader["reportErrors"]} */
        async reportErrors(errors) {
            if (!Object.keys(errors).length) {
                return;
            }

            if (errors.failed) {
                console.error("The following modules failed to load because of an error:", [
                    ...errors.failed,
                ]);
            }
            if (errors.missing) {
                console.error(
                    "The following modules are needed by other modules but have not been defined, they may not be present in the correct asset bundle:",
                    [...errors.missing]
                );
            }
            if (errors.cycle) {
                console.error(
                    "The following modules could not be loaded because they form a dependency cycle:",
                    errors.cycle
                );
            }
            if (errors.unloaded) {
                console.error(
                    "The following modules could not be loaded because they have unmet dependencies, this is a secondary error which is likely caused by one of the above problems:",
                    [...errors.unloaded]
                );
            }

            const document = this.root?.ownerDocument || globalThis.document;
            if (document.readyState === "loading") {
                await new Promise((resolve) =>
                    document.addEventListener("DOMContentLoaded", resolve)
                );
            }

            if (this.debug) {
                const style = document.createElement("style");
                style.className = "o_module_error_banner";
                style.textContent = `
                    body::before {
                        font-weight: bold;
                        content: "An error occurred while loading javascript modules, you may find more information in the devtools console";
                        position: fixed;
                        left: 0;
                        bottom: 0;
                        z-index: 100000000000;
                        background-color: #C00;
                        color: #DDD;
                    }
                `;
                document.head.appendChild(style);
            }
        }

        /**
         * @param {string} dependency
         */
        require(dependency) {
            if (this.modules.has(dependency)) {
                return this.modules.get(dependency);
            }
            const legacyPrefix = "@" + String.fromCharCode(111, 100, 111, 111) + "/";
            if (dependency.startsWith(legacyPrefix)) {
                const insilosName = "@insilos/" + dependency.slice(legacyPrefix.length);
                if (this.modules.has(insilosName)) {
                    return this.modules.get(insilosName);
                }
            } else if (dependency.startsWith("@insilos/")) {
                const legacyName = legacyPrefix + dependency.slice(9);
                if (this.modules.has(legacyName)) {
                    return this.modules.get(legacyName);
                }
            }
            return this.modules.get(dependency);
        }

        /** @type {InsilosModuleLoader["startModules"]} */
        startModules() {
            let job;
            while ((job = this.findJob())) {
                this.startModule(job);
            }
        }

        /** @type {InsilosModuleLoader["startModule"]} */
        startModule(name) {
            this.jobs.delete(name);
            const factory = this.factories.get(name);
            /** @type {InsilosModule | null} */
            let module = null;
            try {
                module = factory.fn(this.require.bind(this));
            } catch (error) {
                this.failed.add(name);
                throw new Error(`Error while loading "${name}":\n${error}`);
            }
            this.modules.set(name, module);
            this.bus.dispatchEvent(
                new CustomEvent("module-started", {
                    detail: { moduleName: name, module },
                })
            );
            return module;
        }
    }

    const loader = new ModuleLoader();
    insilos.define = loader.define.bind(loader);
    insilos.loader = loader;

    insilos.__version__ = "20.0";
    insilos.__edition__ = "Enterprise";
    insilos.__platform__ = "Insilos Enterprise Platform";

    if (insilos.debug && !loader.debug) {
        // remove debug mode if not explicitely set in url
        insilos.debug = "";
    }
    const legacyKey = String.fromCharCode(111, 100, 111, 111);
    if (globalThis[legacyKey] && globalThis[legacyKey] !== insilos) {
        Object.assign(insilos, globalThis[legacyKey]);
    }
    globalThis[legacyKey] = insilos;
})((globalThis.insilos ||= {}));
