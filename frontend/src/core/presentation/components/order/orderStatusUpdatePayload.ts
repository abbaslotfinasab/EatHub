export interface OrderStatusChanges {
    status?: "pending" | "confirmed" | "preparing" | "ready" | "completed" | "cancelled" | "failed";
    paymentStatus?: "pending" | "unpaid" | "paid" | "failed" | "refunded";
    paymentMethod?: "cash" | "card" | "customer_account";
}

export interface OrderStatusDirtyFields {
    status?: boolean;
    paymentStatus?: boolean;
    paymentMethod?: boolean;
}

export interface OrderStatusControlState {
    visible: true;
    disabled: boolean;
    helperText?: string;
}

export function hasPermission(permissionData: unknown, requiredPermission: string): boolean {
    return Array.isArray(permissionData)
        && permissionData.some((permission) => permission === requiredPermission);
}

export function getOrderStatusControlState(permissionData: unknown): OrderStatusControlState {
    const canUpdateOrders = hasPermission(permissionData, "orders.update");

    return {
        visible: true,
        disabled: !canUpdateOrders,
        ...(!canUpdateOrders
            ? {helperText: "برای تغییر وضعیت سفارش، مجوز orders.update لازم است."}
            : {}),
    };
}

export function buildOrderStatusUpdatePayload(
    values: OrderStatusChanges,
    dirty: OrderStatusDirtyFields,
    permissions: {canUpdateOrders: boolean; canManagePayments: boolean},
): OrderStatusChanges {
    return {
        ...(permissions.canUpdateOrders && dirty.status && values.status !== undefined
            ? {status: values.status}
            : {}),
        ...(permissions.canManagePayments && dirty.paymentStatus && values.paymentStatus !== undefined
            ? {paymentStatus: values.paymentStatus}
            : {}),
        ...(permissions.canManagePayments && dirty.paymentMethod && values.paymentMethod !== undefined
            ? {paymentMethod: values.paymentMethod}
            : {}),
    };
}
