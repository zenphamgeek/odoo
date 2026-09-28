insilos.define("@insilos/owl", ["@web/owl2/utils"], function () {
    "use strict";

    return owl;
});
insilos.define("@" + String.fromCharCode(111, 100, 111, 111) + "/owl", ["@insilos/owl"], function (require) {
    "use strict";
    return require("@insilos/owl");
});
