/** @insilos-module alias=@insilos/hoot-mock default=false */

import * as _hootDom from "@insilos/hoot-dom";
import * as _animation from "./mock/animation";
import * as _date from "./mock/date";
import * as _math from "./mock/math";
import * as _navigator from "./mock/navigator";
import * as _network from "./mock/network";
import * as _notification from "./mock/notification";
import * as _window from "./mock/window";

/** @deprecated use `import { advanceFrame } from "@insilos/hoot";` */
export const advanceFrame = _hootDom.advanceFrame;
/** @deprecated use `import { advanceTime } from "@insilos/hoot";` */
export const advanceTime = _hootDom.advanceTime;
/** @deprecated use `import { animationFrame } from "@insilos/hoot";` */
export const animationFrame = _hootDom.animationFrame;
/** @deprecated use `import { cancelAllTimers } from "@insilos/hoot";` */
export const cancelAllTimers = _hootDom.cancelAllTimers;
/** @deprecated use `import { delay } from "@insilos/hoot";` */
export const delay = _hootDom.delay;
/** @deprecated use `import { freezeTime } from "@insilos/hoot";` */
export const freezeTime = _hootDom.freezeTime;
/** @deprecated use `import { microTick } from "@insilos/hoot";` */
export const microTick = _hootDom.microTick;
/** @deprecated use `import { runAllTimers } from "@insilos/hoot";` */
export const runAllTimers = _hootDom.runAllTimers;
/** @deprecated use `import { setFrameRate } from "@insilos/hoot";` */
export const setFrameRate = _hootDom.setFrameRate;
/** @deprecated use `import { tick } from "@insilos/hoot";` */
export const tick = _hootDom.tick;
/** @deprecated use `import { unfreezeTime } from "@insilos/hoot";` */
export const unfreezeTime = _hootDom.unfreezeTime;

/** @deprecated use `import { disableAnimations } from "@insilos/hoot";` */
export const disableAnimations = _animation.disableAnimations;
/** @deprecated use `import { enableTransitions } from "@insilos/hoot";` */
export const enableTransitions = _animation.enableTransitions;

/** @deprecated use `import { mockDate } from "@insilos/hoot";` */
export const mockDate = _date.mockDate;
/** @deprecated use `import { mockLocale } from "@insilos/hoot";` */
export const mockLocale = _date.mockLocale;
/** @deprecated use `import { mockTimeZone } from "@insilos/hoot";` */
export const mockTimeZone = _date.mockTimeZone;
/** @deprecated use `import { onTimeZoneChange } from "@insilos/hoot";` */
export const onTimeZoneChange = _date.onTimeZoneChange;

/** @deprecated use `import { makeSeededRandom } from "@insilos/hoot";` */
export const makeSeededRandom = _math.makeSeededRandom;

/** @deprecated use `import { mockPermission } from "@insilos/hoot";` */
export const mockPermission = _navigator.mockPermission;
/** @deprecated use `import { mockSendBeacon } from "@insilos/hoot";` */
export const mockSendBeacon = _navigator.mockSendBeacon;
/** @deprecated use `import { mockUserAgent } from "@insilos/hoot";` */
export const mockUserAgent = _navigator.mockUserAgent;
/** @deprecated use `import { mockVibrate } from "@insilos/hoot";` */
export const mockVibrate = _navigator.mockVibrate;

/** @deprecated use `import { mockFetch } from "@insilos/hoot";` */
export const mockFetch = _network.mockFetch;
/** @deprecated use `import { mockLocation } from "@insilos/hoot";` */
export const mockLocation = _network.mockLocation;
/** @deprecated use `import { mockWebSocket } from "@insilos/hoot";` */
export const mockWebSocket = _network.mockWebSocket;
/** @deprecated use `import { mockWorker } from "@insilos/hoot";` */
export const mockWorker = _network.mockWorker;

/** @deprecated use `import { flushNotifications } from "@insilos/hoot";` */
export const flushNotifications = _notification.flushNotifications;

/** @deprecated use `import { mockMatchMedia } from "@insilos/hoot";` */
export const mockMatchMedia = _window.mockMatchMedia;
/** @deprecated use `import { mockTouch } from "@insilos/hoot";` */
export const mockTouch = _window.mockTouch;
/** @deprecated use `import { watchAddedNodes } from "@insilos/hoot";` */
export const watchAddedNodes = _window.watchAddedNodes;
/** @deprecated use `import { watchKeys } from "@insilos/hoot";` */
export const watchKeys = _window.watchKeys;
/** @deprecated use `import { watchListeners } from "@insilos/hoot";` */
export const watchListeners = _window.watchListeners;

export { Deferred } from "./hoot";
