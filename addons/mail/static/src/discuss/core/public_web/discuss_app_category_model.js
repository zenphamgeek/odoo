import { compareDatetime } from "@mail/utils/common/misc";
import { fields, Record } from "@mail/core/common/record";

export class DiscussAppCategory extends Record {
    static id = "id";

    sortThreads(t1, t2) {
        if (this.id === "channels") {
            return String.prototype.localeCompare.call(t1.name, t2.name);
        }
        if (this.id === "chats") {
            return compareDatetime(t2.lastInterestDt, t1.lastInterestDt) || t2.id - t1.id;
        }
    }
}

DiscussAppCategory.register();
