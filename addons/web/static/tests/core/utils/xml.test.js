import { describe, expect, test } from "@insilos/hoot";

import { parseXML } from "@web/core/utils/xml";

describe.current.tags("headless");

test("parse error throws an exception", () => {
    expect(() => parseXML("<invalid'>")).toThrow("error occurred while parsing");
    expect(() => parseXML("<div><div>Valid</div><div><Invalid</div></div>")).toThrow(
        "error occurred while parsing"
    );
});
