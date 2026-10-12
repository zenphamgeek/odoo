(() => {
    "use strict";

    const plugins = window.posReactPlugins;
    if (!plugins) return;
    const summary = ({ lines, total, formatMoney }) =>
        `${lines.reduce((quantity, line) => quantity + line.quantity, 0)} items · ${formatMoney(total)}`;

    plugins.register("action", "pos_sale.summary", {
        label: "Sales summary",
        run(context) {
            window.alert(summary(context));
        },
    });
    plugins.register("receiptFragment", "pos_sale.summary", {
        component(context) {
            return window.React.createElement("p", null, summary(context));
        },
    });
})();
