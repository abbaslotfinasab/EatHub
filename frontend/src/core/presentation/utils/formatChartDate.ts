export const formatChartDate = (
    value: string,
): string => {
    return new Intl.DateTimeFormat("fa-IR", {
        month: "numeric",
        day: "numeric",
        timeZone: "Asia/Tehran",
    }).format(new Date(value));
};