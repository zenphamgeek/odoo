import { useService } from "@web/core/utils/hooks";

export const helpers = {
    SUPPORTED_M2X_AVATAR_MODELS: ["res.users", "res.partner"],
    buildOpenChatParams: (resModel, id) => ({
        userId: resModel === "res.users" ? id : undefined,
        partnerId: resModel === "res.partner" ? id : undefined,
    }),
};

export function useOpenChat(resModel) {
    const store = useService("mail.store");
    return async (id) => {
        if (store.openChat) {
            store.openChat(helpers.buildOpenChatParams(resModel, id));
        }
    };
}
