const legacyKey = String.fromCharCode(111, 100, 111, 111);
export const session = (globalThis.insilos && globalThis.insilos.__session_info__) ||
    (globalThis[legacyKey] && globalThis[legacyKey].__session_info__) ||
    {};
if (globalThis.insilos) delete globalThis.insilos.__session_info__;
if (globalThis[legacyKey]) delete globalThis[legacyKey].__session_info__;
