export const formatTime = (
    value?: string | Date | null,
): string => {
    if (!value) return "-";

    return new Intl.DateTimeFormat("fa-IR", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "Asia/Tehran",
    }).format(new Date(value));
};