export const formatCurrency = (
    amount?: number | null,
): string => {
    if (amount == null) return "-";

    return `${new Intl.NumberFormat("fa-IR").format(amount)} تومان`;
};