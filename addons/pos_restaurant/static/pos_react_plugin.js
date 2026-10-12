(() => {
    "use strict";

    const { createElement: h } = React;
    const plugins = window.posReactPlugins;

    function RestaurantScreen({ setScreen }) {
        return h("main", null,
            h("h1", null, "Restaurant"),
            h("button", { onClick: () => setScreen(null) }, "Back")
        );
    }

    function RestaurantSlot() {
        return h("p", null, "Restaurant mode");
    }

    plugins.register("screen", "pos_restaurant.floor", {
        label: "Restaurant",
        component: RestaurantScreen,
    });
    plugins.register("slot", "pos_restaurant.header", {
        slot: "header",
        component: RestaurantSlot,
    });
    plugins.register("dataRequirement", "pos_restaurant.defaults", {
        transform: (data) => ({ ...data, restaurant: data.restaurant || {} }),
    });
})();
