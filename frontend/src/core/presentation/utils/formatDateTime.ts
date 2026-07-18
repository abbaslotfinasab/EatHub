export const formatDateTime = (
    value?: string | Date | null,
): string => {
    if (!value) return "-";

    return new Intl.DateTimeFormat("fa-IR", {
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Tehran",
    }).format(new Date(value));
};