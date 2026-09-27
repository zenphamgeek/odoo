import { serializeDate } from "@web/core/l10n/dates";
import { useService } from "@web/core/utils/hooks";

export function useWorkEntry({ getEmployeeIds, getRange, onClose } = {}) {
    const action = useService("action");
    return {
        onRegenerateWorkEntries: async () => {
            const range = getRange ? getRange() : {};
            const employeeIds = getEmployeeIds ? getEmployeeIds() : [];
            const context = {};
            if (range.start) {
                context.default_date_from = serializeDate(range.start);
            }
            if (range.end) {
                context.default_date_to = serializeDate(range.end);
            }
            if (employeeIds.length === 1) {
                context.default_employee_id = employeeIds[0];
            }
            return action.doAction("hr_work_entry.hr_work_entry_regeneration_wizard_action", {
                additionalContext: context,
                onClose,
            });
        },
    };
}
