import { computed, signal, types as t, untrack, useListener, useOnChange } from "@odoo/owl";
import { useThrottleForAnimation } from "@web/core/utils/timing";

/**
 * Computes the start and end indices of the visible items in a virtual list.
 * This works both horizontally (start = scroll left, span = window width) and
 * vertically (start = scroll top, span = window height).
 *
 * @param {number[]} sizes cumulative sizes of the items
 * @param {number} start starting position (in pixels) of the visible area
 * @param {number} span size (in pixels) of the visible area
 * @param {number} prevStartIndex previous start index, used to optimize the calculation
 * @param {number} bufferCoef coefficient used to compute buffer size
 */
function computeIndices(sizes, start, span, prevStartIndex, bufferCoef) {
    if (!sizes.length) {
        return {
            start: null,
            end: null,
        };
    }
    if (sizes.at(-1) < span) {
        // all items could be displayed
        return {
            start: 0,
            end: sizes.length - 1,
        };
    }
    const bufferSize = Math.ceil(span * bufferCoef);
    const bufferStart = start - bufferSize;
    const bufferEnd = start + span + bufferSize;

    // search the first index such that sizes[index] > bufferStart
    let startIndex = Math.max(0, Math.min(prevStartIndex || 0, sizes.length - 1));
    while (startIndex > 0 && sizes[startIndex] > bufferStart) {
        startIndex--;
    }
    while (startIndex < sizes.length - 1 && sizes[startIndex] <= bufferStart) {
        startIndex++;
    }

    // search the last index such that (sizes[index - 1] || 0) < bufferEnd
    let endIndex = startIndex;
    while (endIndex < sizes.length - 1 && (sizes[endIndex - 1] || 0) < bufferEnd) {
        endIndex++;
    }
    while (endIndex > startIndex && (sizes[endIndex - 1] || 0) >= bufferEnd) {
        endIndex--;
    }

    return {
        start: startIndex,
        end: endIndex,
    };
}

/**
 * @param {number[]} values
 */
function getSummed(values) {
    let acc = 0;
    return values.map((w) => (acc += w));
}

const DEFAULT_BUFFER_COEFFICIENT = 1;

/**
 * Calculates which items should be displayed in a given grid. It works by receiving
 * informations about row widths and/or column heights, and returning the **first**
 * and **last** indices (for each direction) of the items that should be actually
 * rendered.
 *
 * Requirements:
 *  - the scrollable area has a fixed height and width.
 *  - the items are rendered with a proper offset inside the scrollable area.
 *      e.g. using CSS `grid` properties or absolute positioning
 *
 * The returned `scrollableRef` property should be given in a `t-ref` directive
 * to the scrollable element.
 *
 * @param {Object} params
 * @param {import("@odoo/owl").ReactiveValue<HTMLElement>} params.scrollableRef signal
 * @param {number[]} [params.rowHeights] initial row heights
 * @param {number[]} [params.columnWidths] initial column widths
 *  pointing to the scrollable element. It is optional, as this hook can spawn a
 *  new one if needed, that will be available in the return value.
 * @param {{ left?: number; top?: number }} [params.initialScroll] initial scroll
 *  position of the scrollable element
 * @param {number} [params.bufferCoef=1] coefficient used to calculate the buffer
 *  size around the visible area; with its default value of 1, it means that the
 *  resulting buffer size is equal to the size of the window, and that the whole
 *  rendered area will be 3 times the window size.
 *  As this works in both dimensions, this could mean that a total area of 9 windows
 *  (3x3) would be rendered.
 *  Consider using a lower value if the rendering becomse too costly.
 *  Setting it to 0 removes the buffer entirely.
 */
export function useVirtualGrid({
    scrollableRef,
    rowHeights,
    columnWidths,
    initialScroll,
    bufferCoef,
    onChange,
}) {
    function onResize() {
        innerWidth.set(window.innerWidth);
        innerHeight.set(window.innerHeight);
    }

    /**
     * @param {Event & { currentTarget: HTMLElement }} ev
     */
    function onScroll(ev) {
        scrollLeft.set(ev.currentTarget.scrollLeft);
        scrollTop.set(ev.currentTarget.scrollTop);
    }

    bufferCoef ||= DEFAULT_BUFFER_COEFFICIENT;

    // Columns reactive values
    const columnIndices = computed(function computeColumnIndices() {
        const indices = computeIndices(
            summedColumnWidths(),
            Math.abs(scrollLeft()),
            innerWidth(),
            lastColumnStartIndex,
            bufferCoef
        );
        lastColumnStartIndex = indices.start;
        return indices;
    });
    const firstColumn = computed(() => columnIndices().start);
    const lastColumn = computed(() => columnIndices().end);
    const summedColumnWidths = signal.Array(getSummed(columnWidths || []), t.number());
    let lastColumnStartIndex = 0;

    // Rows reactive values
    const rowIndices = computed(function computeRowIndices() {
        const indices = computeIndices(
            summedRowHeights(),
            Math.abs(scrollTop()),
            innerHeight(),
            lastRowStartIndex,
            bufferCoef
        );
        lastRowStartIndex = indices.start;
        return indices;
    });
    const firstRow = computed(() => rowIndices().start);
    const lastRow = computed(() => rowIndices().end);
    const summedRowHeights = signal.Array(getSummed(rowHeights || []), t.number());
    let lastRowStartIndex = 0;

    // "External" reactive values (i.e.: scroll position & window size)
    const innerWidth = signal(window.innerWidth);
    const innerHeight = signal(window.innerHeight);
    const scrollLeft = signal(initialScroll?.left || 0);
    const scrollTop = signal(initialScroll?.top || 0);

    useListener(scrollableRef, "scroll", useThrottleForAnimation(onScroll));
    useListener(window, "resize", useThrottleForAnimation(onResize));

    let initialized = false;
    let prevColStart = null;
    let prevColEnd = null;
    let prevRowStart = null;
    let prevRowEnd = null;

    if (onChange) {
        useOnChange(
            () => [firstColumn(), lastColumn(), firstRow(), lastRow()],
            (colStart, colEnd, rowStart, rowEnd) => {
                if (colStart === null && rowStart === null) {
                    return;
                }
                if (!initialized) {
                    initialized = true;
                    prevColStart = colStart;
                    prevColEnd = colEnd;
                    prevRowStart = rowStart;
                    prevRowEnd = rowEnd;
                    return;
                }
                const changed = {};
                if (colStart !== prevColStart || colEnd !== prevColEnd) {
                    prevColStart = colStart;
                    prevColEnd = colEnd;
                    changed.columnsIndexes = [colStart, colEnd];
                }
                if (rowStart !== prevRowStart || rowEnd !== prevRowEnd) {
                    prevRowStart = rowStart;
                    prevRowEnd = rowEnd;
                    changed.rowsIndexes = [rowStart, rowEnd];
                }
                if (Object.keys(changed).length) {
                    onChange(changed);
                }
            },
            { initialRun: false }
        );
    }

    return {
        firstRow,
        lastRow,
        firstColumn,
        lastColumn,
        get columnsIndexes() {
            return untrack(() => [firstColumn(), lastColumn()]);
        },
        get rowsIndexes() {
            return untrack(() => [firstRow(), lastRow()]);
        },
        /**
         * Sets the width of each column.
         * Indexes should match the indexes of the columns.
         *
         * @param {number[]} widths
         */
        setColumnWidths(widths) {
            lastColumnStartIndex = 0;
            summedColumnWidths.set(getSummed(widths));
            prevColStart = firstColumn();
            prevColEnd = lastColumn();
        },
        setColumnsWidths(widths) {
            this.setColumnWidths(widths);
        },
        /**
         * Sets the height of each row.
         * Indexes should match the indexes of the rows.
         *
         * @param {number[]} heights
         */
        setRowHeights(heights) {
            lastRowStartIndex = 0;
            summedRowHeights.set(getSummed(heights));
            prevRowStart = firstRow();
            prevRowEnd = lastRow();
        },
        setRowsHeights(heights) {
            this.setRowHeights(heights);
        },
    };
}
