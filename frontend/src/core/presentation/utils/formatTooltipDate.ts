import {formatDate} from "./formatDate.ts";

export const formatTooltipDate = (
    label: unknown,
): string => {

    if (typeof label === "string" || label instanceof Date) {
        return formatDate(label);
    }

    return "-";
};