import {
    Component,
    onMounted,
    onPatched,
    onWillDestroy,
    proxy,
    signal,
    useEffect,
    useListener,
    usePlugin,
    useScope,
} from "@insilos/owl";
import { DebugModePlugin } from "@web/core/debug_mode_plugin";
import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownGroup } from "@web/core/dropdown/dropdown_group";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { OfflinePlugin } from "@web/core/offline/offline_plugin";
import { registry } from "@web/core/registry";
import { Transition } from "@web/core/transition";
import { ErrorHandler } from "@web/core/utils/components";
import { useService } from "@web/core/utils/hooks";
import { debounce } from "@web/core/utils/timing";
import { render } from "@web/owl2/utils";

const systrayRegistry = registry.category("systray");

const getBoundingClientRect = Element.prototype.getBoundingClientRect;

const SWIPE_ACTIVATION_THRESHOLD = 100;

export class MenuDropdown extends Dropdown {}

export class NavBar extends Component {
    static template = "web.NavBar";
    static components = {
        Dropdown,
        DropdownItem,
        DropdownGroup,
        MenuDropdown,
        ErrorHandler,
        Transition,
    };
    root = signal.ref();
    appSubMenus = signal.ref();
    menuApps = signal.ref();

    debugMode = usePlugin(DebugModePlugin);

    scope = useScope();
    isAdapting = false;

    setup() {
        this.isAdapting = false;
        this.currentAppSectionsExtra = [];
        this.actionService = useService("action");
        this.menuService = useService("menu");
        this.offlinePlugin = usePlugin(OfflinePlugin);
        this.pwa = useService("pwa");
        const debouncedAdapt = debounce(this.adapt.bind(this), 100);
        onWillDestroy(() => debouncedAdapt.cancel());
        useListener(window, "resize", debouncedAdapt);

        // The sections menu's width shrinks/grows when the breadcrumbs get longer or when
        // a systray item changes size (e.g. the offline item displaying "Working offline").
        let sectionsWidth = null;
        const sectionsObserver = new ResizeObserver(([entry]) => {
            const { inlineSize } = entry.borderBoxSize[0];
            if (inlineSize !== sectionsWidth) {
                sectionsWidth = inlineSize;
                debouncedAdapt();
            }
        });
        useEffect(() => {
            const sectionsMenu = this.appSubMenus();
            if (!sectionsMenu) {
                return;
            }
            // the initial observation notifies the current size: ignore it
            sectionsWidth = getBoundingClientRect.call(sectionsMenu).width;
            sectionsObserver.observe(sectionsMenu);
            return () => sectionsObserver.disconnect();
        });

        let adaptOnNextPatch = false;
        const renderAndAdapt = () => {
            adaptOnNextPatch = true;
            render(this);
        };

        useListener(systrayRegistry, "UPDATE", renderAndAdapt);
        useListener(this.env.bus, "MENUS:APP-CHANGED", renderAndAdapt);

        onMounted(() => {
            adaptOnNextPatch = false;
            this.adapt();
        });
        onPatched(() => {
            if (adaptOnNextPatch) {
                adaptOnNextPatch = false;
                this.adapt();
            }
        });

        this.state = proxy({
            isAllAppsMenuOpened: false,
            isAppMenuSidebarOpened: false,
        });
        this.ui = proxy(useService("ui"));
    }

    handleItemError(error, item) {
        // remove the faulty component
        item.isDisplayed = () => false;
        Promise.resolve().then(() => {
            throw error;
        });
    }

    get currentApp() {
        const app = this.menuService.getCurrentApp();
        if (app?.webIcon) {
            const [webIconClass, webIconColor, webIconBg] = app.webIcon.split(",");
            return {
                ...app,
                webIconClass,
                webIconColor,
                webIconBg,
            };
        }
        return app;
    }

    get currentAppSections() {
        return (
            (this.currentApp && this.menuService.getMenuAsTree(this.currentApp.id).childrenTree) ||
            []
        );
    }

    // This dummy setter is only here to prevent conflicts between the
    // Enterprise NavBar extension and the Website NavBar patch.
    set currentAppSections(_) {}

    get isScopedApp() {
        return this.pwa.isScopedApp;
    }

    get systrayItems() {
        return systrayRegistry
            .getEntries()
            .map(([key, value]) => ({ key, ...value }))
            .filter((item) =>
                "isDisplayed" in item ? this.scope.run(() => item.isDisplayed(this.env)) : true
            )
            .reverse();
    }

    // This dummy setter is only here to prevent conflicts between the
    // Enterprise NavBar extension and the Website NavBar patch.
    set systrayItems(_) {}

    /**
     * Adapt will check the available width for the app sections to get displayed.
     * If not enough space is available, it will replace by a "more" menu
     * the least amount of app sections needed trying to fit the width.
     *
     * NB: To compute the widths of the actual app sections, a render needs to be done upfront.
     *     By the end of this method another render may occur depending on the adaptation result.
     */
    async adapt() {
        if (!this.root() || this.isAdapting) {
            /** @todo do we still need this check? */
            // currently, the promise returned by 'render' is resolved at the end of
            // the rendering even if the component has been destroyed meanwhile, so we
            // may get here and have this.el unset
            return;
        }

        // ------- Initialize -------
        // Get the sectionsMenu
        const sectionsMenu = this.appSubMenus();
        if (!sectionsMenu) {
            // No need to continue adaptations if there is no sections menu.
            return;
        }

        this.isAdapting = true;
        try {
            // Save initial state to further check if new render has to be done.
            const initialAppSectionsExtra = this.currentAppSectionsExtra;
            const initialSectionIds = initialAppSectionsExtra
                .map((s) => `${s?.appID || ""}:${s?.id}`)
                .join(",");

            // Restore (needed to get offset widths)
            const sections = [
                ...sectionsMenu.querySelectorAll(":scope > *:not(.o_menu_sections_more)"),
            ];
            for (const section of sections) {
                section.classList.remove("d-none");
            }
            this.currentAppSectionsExtra = [];

            // ------- Check overflowing sections -------
            // Calculate true physical geometric available space bounded by Brand and Systray
            const navEl = this.root()?.querySelector(".o_main_navbar") || this.root();
            const systrayEl = navEl?.querySelector(".o_menu_systray");
            const brandEl =
                navEl?.querySelector(".o_menu_brand_wrapper") ||
                navEl?.querySelector(".o_menu_brand");

            const sectionsRect = getBoundingClientRect.call(sectionsMenu);
            let sectionsAvailableWidth = sectionsRect.width;

            if (navEl && systrayEl) {
                const navRect = getBoundingClientRect.call(navEl);
                const systrayRect = getBoundingClientRect.call(systrayEl);
                const navStyle = window.getComputedStyle(navEl);
                const paddingRight = parseFloat(navStyle.paddingRight) || 0;

                // Physical right boundary where sections must stop before hitting systray
                const maxRight = navRect.right - paddingRight - systrayRect.width;

                // Physical left boundary where sections start (after brand wrapper)
                const brandRight = brandEl
                    ? getBoundingClientRect.call(brandEl).right
                    : sectionsRect.left;
                const effectiveLeft = Math.max(sectionsRect.left, brandRight);

                // Safety buffer of 12px absorbs subpixel rounding, flex gaps, and borders
                const safetyBuffer = 12;
                const geometricSpace = Math.max(0, maxRight - effectiveLeft - safetyBuffer);

                // Bound sectionsAvailableWidth by physical geometric free space
                sectionsAvailableWidth = Math.min(sectionsRect.width, geometricSpace);
            }

            const sectionsTotalWidth = sections.reduce(
                (sum, s) => sum + getBoundingClientRect.call(s).width,
                0
            );

            if (sectionsAvailableWidth < sectionsTotalWidth) {
                // Determine accurate reserved width for the More button (min 58px)
                const moreBtn = sectionsMenu.querySelector(".o_menu_sections_more");
                let moreReservedWidth = 58;
                if (moreBtn) {
                    const measured = getBoundingClientRect.call(moreBtn).width;
                    if (measured > 0) {
                        moreReservedWidth = Math.max(58, Math.ceil(measured));
                    }
                }

                let width = moreReservedWidth;
                for (const section of sections) {
                    const sectionWidth = getBoundingClientRect.call(section).width;
                    if (sectionsAvailableWidth < width + sectionWidth) {
                        // Last sections are overflowing
                        const overflowingSections = sections.slice(sections.indexOf(section));
                        overflowingSections.forEach((s) => {
                            // Hide from normal menu
                            s.classList.add("d-none");
                            // Show inside "more" menu
                            const sectionId =
                                s.dataset.section ||
                                s.querySelector("[data-section]")?.getAttribute("data-section");
                            const currentAppSection = this.currentAppSections.find(
                                (appSection) => appSection.id.toString() === sectionId
                            );
                            if (
                                currentAppSection &&
                                !this.currentAppSectionsExtra.includes(currentAppSection)
                            ) {
                                this.currentAppSectionsExtra.push(currentAppSection);
                            }
                        });
                        break;
                    }
                    width += sectionWidth;
                }
            }

            // ------- Final rendering -------
            const currentSectionIds = this.currentAppSectionsExtra
                .map((s) => `${s?.appID || ""}:${s?.id}`)
                .join(",");
            if (
                initialAppSectionsExtra.length === this.currentAppSectionsExtra.length &&
                initialSectionIds === currentSectionIds
            ) {
                // Do not render if more menu items stayed the same.
                return;
            }
            this.render();
        } finally {
            this.isAdapting = false;
        }
    }

    render() {
        render(this);
    }

    onNavBarDropdownItemSelection(menu) {
        if (menu) {
            this.menuService.selectMenu(menu);
        }
    }

    getMenuItemHref(payload) {
        const url = `/insilos/${payload.actionPath || "action-" + payload.actionID}`;
        const mode = this.debugMode.toString();
        if (mode) {
            return `${url}?debug=${mode}`;
        }
        return url;
    }

    _closeAppMenuSidebar() {
        this.state.isAllAppsMenuOpened = false;
        this.state.isAppMenuSidebarOpened = false;
    }
    _openAppMenuSidebar() {
        this.state.isAppMenuSidebarOpened = !this.state.isAppMenuSidebarOpened;
    }

    _isAvailable(menu) {
        return (
            !this.offlinePlugin.isOffline() ||
            !menu.actionID ||
            this.offlinePlugin.isAvailableOffline(menu.actionID)
        );
    }

    onAllAppsBtnClick() {
        this.state.isAllAppsMenuOpened = !this.state.isAllAppsMenuOpened;
    }
    async _onMenuClicked(menu) {
        await this.menuService.selectMenu(menu);
        this._closeAppMenuSidebar();
    }
    _onSwipeStart(ev) {
        this.swipeStartX = ev.changedTouches[0].clientX;
    }
    _onSwipeEnd(ev) {
        if (!this.swipeStartX) {
            return;
        }
        const deltaX = this.swipeStartX - ev.changedTouches[0].clientX;
        if (deltaX < SWIPE_ACTIVATION_THRESHOLD) {
            return;
        }
        this._closeAppMenuSidebar();
        this.swipeStartX = null;
    }
}
