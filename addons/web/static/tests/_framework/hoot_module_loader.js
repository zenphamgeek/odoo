// @insilos-module ignore
// ! WARNING: this module must be loaded after `module_loader` but cannot have dependencies !

(function (insilos) {
    "use strict";

    if (insilos.define.name.endsWith("(hoot)")) {
        return;
    }

    const name = `${insilos.define.name} (hoot)`;
    insilos.define = {
        [name](name, dependencies, factory) {
            return insilos.loader.define(name, dependencies, factory, !name.endsWith(".hoot"));
        },
    }[name];
    if (globalThis[String.fromCharCode(111, 100, 111, 111)]) {
        globalThis[String.fromCharCode(111, 100, 111, 111)].define = insilos.define;
    }
})(globalThis.insilos);
