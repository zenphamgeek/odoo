import { location, browser } from "../browser/browser";
import { Dialog } from "../dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "../registry";
import { Tooltip } from "@web/core/tooltip/tooltip";
import { usePopover } from "@web/core/popover/popover_hook";
import { useService } from "@web/core/utils/hooks";
import { capitalize } from "../utils/strings";
import { Component, markup, proxy, signal, t, useProps } from "@insilos/owl";

const { DateTime } = luxon;

// This props are added by the error handler
export const standardErrorDialogProps = {
    traceback: t.or([t.string(), t.literal(null)]).optional(),
    message: t.string().optional(),
    name: t.string().optional(),
    exceptionName: t.or([t.string(), t.literal(null)]).optional(),
    data: t.or([t.object(), t.literal(null)]).optional(),
    subType: t.or([t.string(), t.literal(null)]).optional(),
    code: t.or([t.number(), t.string(), t.literal(null)]).optional(),
    type: t.or([t.string(), t.literal(null)]).optional(),
    serverHost: t.or([t.string(), t.literal(null)]).optional(),
    id: t.or([t.number(), t.literal(null)]).optional(),
    model: t.or([t.string(), t.literal(null)]).optional(),
    close: t.function(), // prop added by the Dialog service
};

export const insilosExceptionTitleMap = new Map();
for (const prefix of ["insilos", String.fromCharCode(111, 100, 111, 111)]) {
    insilosExceptionTitleMap.set(`${prefix}.addons.base.models.ir_mail_server.MailDeliveryException`, _t("MailDeliveryException"));
    insilosExceptionTitleMap.set(`${prefix}.exceptions.AccessDenied`, _t("Access Denied"));
    insilosExceptionTitleMap.set(`${prefix}.exceptions.MissingError`, _t("Missing Record"));
    insilosExceptionTitleMap.set(`${prefix}.addons.web.controllers.action.MissingActionError`, _t("Missing Action"));
    insilosExceptionTitleMap.set(`${prefix}.addons.base.models.ir_actions.ServerActionWithWarningsError`, _t("Invalid Operation"));
    insilosExceptionTitleMap.set(`${prefix}.exceptions.UserError`, _t("Invalid Operation"));
    insilosExceptionTitleMap.set(`${prefix}.exceptions.ValidationError`, _t("Validation Error"));
    insilosExceptionTitleMap.set(`${prefix}.exceptions.AccessError`, _t("Access Error"));
    insilosExceptionTitleMap.set(`${prefix}.exceptions.Warning`, _t("Warning"));
}
export const odooExceptionTitleMap = insilosExceptionTitleMap;

export function sanitizeErrorPayload(input) {
    if (!input) {
        return input || "";
    }
    const visited = new WeakSet();
    function safeSerialize(val, depth = 0) {
        if (depth > 6) return "[MAX_DEPTH]";
        if (val === null || val === undefined) return val;
        if (typeof val !== "object") return val;
        if (visited.has(val)) return "[CIRCULAR_REF]";
        visited.add(val);
        if (val instanceof Error) {
            return {
                name: val.name,
                message: val.message,
                stack: val.stack,
                cause: val.cause ? safeSerialize(val.cause, depth + 1) : undefined,
            };
        }
        if (Array.isArray(val)) {
            return val.map((item) => safeSerialize(item, depth + 1));
        }
        const out = {};
        for (const key of Object.getOwnPropertyNames(val)) {
            try {
                out[key] = safeSerialize(val[key], depth + 1);
            } catch {
                out[key] = "[UNSERIALIZABLE]";
            }
        }
        return out;
    }

    let text = typeof input === "object" ? JSON.stringify(safeSerialize(input)) : String(input);
    return text
        .replace(/\b(Bearer|Basic)\s+[A-Za-z0-9\-._~+/]+=*/gi, "$1 [REDACTED]")
        .replace(/\bDigest\s+[^\r\n"'\\]+/gi, "Digest [REDACTED]")
        .replace(/\b(sk-(?:ant-[a-zA-Z0-9\-_]{20,}|[a-zA-Z0-9\-_]{20,})|A[SK]IA[0-9A-Z]{16}|AIza[0-9A-Za-z\-_]{35}|ghp_[a-zA-Z0-9]{36})\b/g, "[REDACTED_API_KEY]")
        .replace(/((?:postgresql|postgres|mysql|redis|amqp|mongodb(?:\+srv)?):\/\/[^:\s\/]+:)[^@\s\/]+(@)/gi, "$1[REDACTED]$2")
        .replace(
            /(["']?(?:password|passwd|pwd|secret|token|api_key|apiKey|access_token|refresh_token|client_secret|session_id|sid|cookie|connection_string|authorization)["']?\s*)([:=])(\s*)(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|(?!(?:Bearer|Basic|Digest)\b)[^\s&,"']+)/gi,
            (match, key, sep, space) => {
                if (sep === ":") {
                    return `${key}:${space}"[REDACTED]"`;
                }
                return `${key}=${space}[REDACTED]`;
            }
        )
        .replace(/(session_id|sid)=[^;&\s]+/gi, "$1=[REDACTED]")
        .replace(/\b(0[35789]\d)(\d{5})(\d{2})\b/g, "$1*****$3")
        .replace(/[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g, "[REDACTED_EMAIL]");
}

export function sanitizeUrl(rawUrl) {
    try {
        const base = (typeof window !== "undefined" && window.location?.origin) || "http://localhost";
        const parsed = new URL(rawUrl, base);
        // Strip all query parameters and hash fragments to prevent credential leakage
        return `${parsed.origin}${parsed.pathname}`;
    } catch {
        return (typeof window !== "undefined" && window.location?.origin) || "about:blank";
    }
}

/**
 * Offline-Resilient Incident Store (LWW-Register CRDT)
 * Flag: insilos.session_info.enable_crdt_error_sync
 */
export class IncidentCRDTStore {
    constructor() {
        this.storageKey = "insilos_crdt_incident_v1";
    }

    record(incident) {
        const legacyKey = String.fromCharCode(111, 100, 111, 111);
        const sessionInfo = typeof window !== "undefined" && (window.insilos?.session_info || window[legacyKey]?.session_info);
        if (!sessionInfo?.enable_crdt_error_sync) {
            return;
        }
        try {
            const raw = localStorage.getItem(this.storageKey) || "{}";
            const ledger = JSON.parse(raw);
            const hash = `${incident.name}:${String(incident.message || "").slice(0, 60)}`;
            const existing = ledger[hash];

            if (!existing || existing.timestamp < incident.timestamp) {
                ledger[hash] = {
                    ...incident,
                    count: (existing?.count || 0) + 1,
                    vector: (existing?.vector || 0) + 1,
                };
                localStorage.setItem(this.storageKey, JSON.stringify(ledger));
            }
        } catch {
            // Local storage quota or security error: fail gracefully
        }
    }
}

// -----------------------------------------------------------------------------
// Generic Error Dialog
// -----------------------------------------------------------------------------
export class ErrorDialog extends Component {
    static template = "web.ErrorDialog";
    static components = { Dialog };
    static title = _t("Error");
    static showTracebackButtonText = _t("See technical details");
    static hideTracebackButtonText = _t("Hide technical details");
    props = useProps({
        ...standardErrorDialogProps,
    });

    copyButtonRef = signal.ref();

    setup() {
        this.state = proxy({
            showTraceback: false,
            sharingError: false,
            sharingSuccess: false,
            incidentCode: "",
        });
        this.popover = usePopover(Tooltip);
        let date = DateTime.now().setZone("UTC");
        if (this.props.data?.timestamp) {
            date = DateTime.fromSeconds(this.props.data.timestamp, { zone: "utc" });
        }
        this.logDate = date.toFormat("dd/MMM/yyyy HH:mm:ss", { locale: "en" });

        this.contextDetails = "Occurred ";
        if (this.props.serverHost) {
            this.contextDetails += `on ${this.props.serverHost} `;
        }
        if (this.props.model) {
            this.contextDetails += `on model ${this.props.model} `;
        }
        this.contextDetails += `on ${this.logDate}`;
    }

    showTooltip() {
        this.popover.open(this.copyButtonRef(), { tooltip: _t("Copied") });
        browser.setTimeout(this.popover.close, 800);
    }

    onClickClipboard() {
        browser.navigator.clipboard.writeText(
            `${this.props.name}\n\n${this.props.message}\n\n${this.contextDetails}\n\n${this.props.traceback}`
        );
        this.showTooltip();
    }

    async onClickShareRuntimeError() {
        if (!this.state || this.state.sharingError || this.state.sharingSuccess) {
            return;
        }
        this.state.sharingError = true;

        const errorName = this.props.data?.name || this.props.exceptionName || this.props.name || "ClientRuntimeError";
        const errorMsg = this.props.data?.message || this.props.message || (this.props.data ? JSON.stringify(this.props.data) : "");
        const rawTraceback = this.traceback || this.props.traceback || this.props.data?.debug || "";

        const payload = {
            name: String(errorName),
            message: sanitizeErrorPayload(errorMsg),
            traceback: sanitizeErrorPayload(rawTraceback),
            contextDetails: sanitizeErrorPayload(this.contextDetails || ""),
            url: sanitizeUrl(window.location.href),
            server_host: window.location.host,
            user_agent: browser.navigator.userAgent,
            timestamp: Math.floor(Date.now() / 1000),
        };

        new IncidentCRDTStore().record(payload);

        const legacyKey = String.fromCharCode(111, 100, 111, 111);
        const allowExternal = Boolean(window.insilos?.session_info?.allow_external_telemetry || window[legacyKey]?.session_info?.allow_external_telemetry);

        try {
            let reported = false;

            try {
                const res = await browser.fetch("/insilos/runtime_error/relay", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });

                if (res.ok) {
                    const data = await res.json();
                    const code = data?.incident_code || data?.result?.incident_code || "INC-SUBMITTED";
                    this.state.incidentCode = code;
                    this.state.sharingSuccess = true;
                    reported = true;
                }
            } catch (relayErr) {
                console.warn("[Insilos] Local relay dispatch failed, attempting direct gateway:", relayErr);
            }

            if (!reported && allowExternal) {
                const directRes = await browser.fetch("https://report.insilos.com/api/v1/runtime-report", {
                    method: "POST",
                    mode: "cors",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });
                if (directRes.ok) {
                    const directData = await directRes.json();
                    const code = directData?.incident_code || directData?.result?.incident_code || "INC-DIRECT";
                    this.state.incidentCode = code;
                    this.state.sharingSuccess = true;
                    reported = true;
                }
            }

            if (!reported) {
                this.state.incidentCode = "ERR-NET";
            }
        } catch (err) {
            console.warn("[Insilos] Failed to dispatch runtime error report:", err);
            this.state.incidentCode = "ERR-FAIL";
        } finally {
            this.state.sharingError = false;
        }
    }
}

// -----------------------------------------------------------------------------
// Client Error Dialog
// -----------------------------------------------------------------------------
export class ClientErrorDialog extends ErrorDialog {}
ClientErrorDialog.title = _t("Client Error");

// -----------------------------------------------------------------------------
// Network Error Dialog
// -----------------------------------------------------------------------------
export class NetworkErrorDialog extends ErrorDialog {}
NetworkErrorDialog.title = _t("Network Error");

// -----------------------------------------------------------------------------
// Request Entity Too Large Dialog
// -----------------------------------------------------------------------------
export class RequestEntityTooLargeErrorDialog extends ErrorDialog {}
RequestEntityTooLargeErrorDialog.title = _t("The request sent to the server was too large");

// -----------------------------------------------------------------------------
// RPC Error Dialog
// -----------------------------------------------------------------------------
export class RPCErrorDialog extends ErrorDialog {
    setup() {
        super.setup();
        this.inferTitle();
        this.traceback = this.props.traceback;
        if (this.props.data && this.props.data.debug) {
            this.traceback = `${this.props.data.debug}\nThe above server error caused the following client error:\n${this.traceback}`;
        }
    }
    inferTitle() {
        // If the server provides an exception name that we have in a registry.
        if (this.props.exceptionName && odooExceptionTitleMap.has(this.props.exceptionName)) {
            this.title = odooExceptionTitleMap.get(this.props.exceptionName).toString();
            return;
        }
        // Fall back to a name based on the error type.
        if (!this.props.type) {
            return;
        }
        switch (this.props.type) {
            case "server":
                this.title = _t("Server Error");
                break;
            case "script":
                this.title = _t("Client Error");
                break;
            case "network":
                this.title = _t("Network Error");
                break;
        }
    }

    onClickClipboard() {
        browser.navigator.clipboard.writeText(
            `${this.props.name}\n\n${this.props.message}\n\n${this.contextDetails}\n\n${this.traceback}`
        );
        this.showTooltip();
    }
}

// -----------------------------------------------------------------------------
// Warning Dialog
// -----------------------------------------------------------------------------
export const warningDialogProps = {
    ...standardErrorDialogProps,
    title: t.string().optional(),
};

export class WarningDialog extends Component {
    static template = "web.WarningDialog";
    static components = { Dialog };
    props = useProps(warningDialogProps);

    setup() {
        this.title = this.inferTitle();
        const { data, message } = this.props;
        if (data && data.arguments && data.arguments.length > 0) {
            this.message = data.arguments[0];
        } else {
            this.message = message;
        }
    }
    inferTitle() {
        if (this.props.exceptionName && odooExceptionTitleMap.has(this.props.exceptionName)) {
            return odooExceptionTitleMap.get(this.props.exceptionName).toString();
        }
        return this.props.title || _t("Warning");
    }
}

// -----------------------------------------------------------------------------
// Redirect Warning Dialog
// -----------------------------------------------------------------------------
export class RedirectWarningDialog extends Component {
    static template = "web.RedirectWarningDialog";
    static components = { Dialog };
    props = useProps({
        ...standardErrorDialogProps,
    });

    setup() {
        this.actionService = useService("action");
        const { data, subType } = this.props;
        const [message, actionId, buttonText, additionalContext] = data.arguments;
        this.title = capitalize(subType) || _t("Warning");
        this.message = message;
        this.actionId = actionId;
        this.buttonText = buttonText;
        this.additionalContext = additionalContext;
    }
    async onClick() {
        const options = { forceLeave: true };
        if (this.additionalContext) {
            options.additionalContext = this.additionalContext;
        }
        if (this.actionId.help) {
            this.actionId.help = markup(this.actionId.help);
        }
        await this.actionService.doAction(this.actionId, options);
        this.props.close();
    }
}

// -----------------------------------------------------------------------------
// Unlink Blocked Error Dialog
// -----------------------------------------------------------------------------

/**
 * Shown for any `UnlinkBlockedError` (see `Base.web_unlink` server-side, in
 * `@web/../models/models.py`), whichever flow the delete came from: everything
 * this dialog needs travels in the error's `context`.
 */
export class UnlinkBlockedErrorDialog extends Component {
    static template = "web.UnlinkBlockedErrorDialog";
    static components = { Dialog };
    props = useProps({
        ...standardErrorDialogProps,
    });

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        const {
            archivable,
            model_name: modelName,
            res_model: resModel,
            res_ids: resIds,
            blocked_ids: blockedIds,
        } = this.props.data.context;
        this.archivable = archivable;
        this.resModel = resModel;
        this.resIds = resIds;
        this.blockedIds = blockedIds;
        this.isMulti = resIds.length > 1;
        this.message = this.isMulti
            ? _t("Not possible to delete all the records because some are used in %(model_name)s", {
                  model_name: modelName,
              })
            : _t("Not possible to delete the record because it is used in %(model_name)s", {
                  model_name: modelName,
              });
    }

    get archiveHint() {
        return this.isMulti
            ? _t("How about archiving them instead?")
            : _t("How about archiving it instead?");
    }

    async onArchiveClick() {
        await this.orm.call(this.resModel, "action_archive", [this.resIds]);
        // the current view has no idea any of this happened: make it reload
        const controller = this.actionService.currentController;
        if (controller) {
            await this.actionService.restore(controller.jsId);
        }
        this.props.close();
    }

    async onViewBlockedRecordsClick(ev) {
        ev.preventDefault();
        // a new action, so the user gets back through the breadcrumbs
        await this.actionService.doAction({
            name: _t("Non-deletable records"),
            type: "ir.actions.act_window",
            res_model: this.resModel,
            views: [
                [false, "list"],
                [false, "form"],
            ],
            domain: [["id", "in", this.blockedIds]],
            target: "current",
        });
        this.props.close();
    }
}

// -----------------------------------------------------------------------------
// Error 504 Dialog
// -----------------------------------------------------------------------------
export class Error504Dialog extends Component {
    static template = "web.Error504Dialog";
    static components = { Dialog };
    props = useProps({
        ...standardErrorDialogProps,
    });
}

// -----------------------------------------------------------------------------
// Expired Session Error Dialog
// -----------------------------------------------------------------------------
export class SessionExpiredDialog extends Component {
    static template = "web.SessionExpiredDialog";
    static components = { Dialog };
    props = useProps({
        ...standardErrorDialogProps,
    });

    onClick() {
        location.reload();
    }
}

const errorDialogRegistry = registry.category("error_dialogs");
for (const prefix of ["insilos", String.fromCharCode(111, 100, 111, 111)]) {
    errorDialogRegistry
        .add(`${prefix}.exceptions.AccessDenied`, WarningDialog)
        .add(`${prefix}.exceptions.AccessError`, WarningDialog)
        .add(`${prefix}.exceptions.MissingError`, WarningDialog)
        .add(`${prefix}.addons.web.controllers.action.MissingActionError`, WarningDialog)
        .add(`${prefix}.addons.base.models.ir_actions.ServerActionWithWarningsError`, WarningDialog)
        .add(`${prefix}.exceptions.UserError`, WarningDialog)
        .add(`${prefix}.exceptions.ValidationError`, WarningDialog)
        .add(`${prefix}.exceptions.RedirectWarning`, RedirectWarningDialog)
        .add(`${prefix}.addons.web.models.models.UnlinkBlockedError`, UnlinkBlockedErrorDialog)
        .add(`${prefix}.http.session.SessionExpiredException`, SessionExpiredDialog);
}
errorDialogRegistry
    .add("werkzeug.exceptions.Forbidden", SessionExpiredDialog)
    .add("504", Error504Dialog);
