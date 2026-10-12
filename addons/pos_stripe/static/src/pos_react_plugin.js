(() => {
    "use strict";

    const plugins = window.posReactPlugins;
    if (!plugins) return;

    plugins.register("paymentAdapter", "stripe", {
        label: "Stripe",
        async start(context) {
            const terminal = context?.pluginData?.terminal;
            const payment = context?.pluginData?.payment;
            if (!terminal || !payment || typeof terminal.collectPaymentMethod !== "function") {
                return false;
            }
            return terminal.collectPaymentMethod(payment);
        },
    });
})();
