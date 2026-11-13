import type {QueryClient} from "@tanstack/react-query";

import {orderQueryKeys} from "./orderQueryKeys.ts";

export interface OrderQueryScope {
    userId: number | null;
    businessId: number | null;
}

export type OrderMutationKind =
    | "create"
    | "update"
    | "delete"
    | "status"
    | "refund"
    | "consumption";

interface OrderQueryInvalidationTargets {
    list?: boolean;
    detail?: boolean;
    statusHistory?: boolean;
    consumption?: boolean;
    refund?: boolean;
}

const invalidationTargets: Record<OrderMutationKind, OrderQueryInvalidationTargets> = {
    create: {list: true},
    update: {list: true, detail: true},
    delete: {list: true, detail: true, statusHistory: true, consumption: true, refund: true},
    status: {list: true, detail: true, statusHistory: true, consumption: true, refund: true},
    refund: {list: true, detail: true, statusHistory: true, refund: true},
    consumption: {detail: true, consumption: true},
};

export const invalidateOrderQueries = async (
    queryClient: QueryClient,
    scope: OrderQueryScope,
    orderId: string | undefined,
    mutation: OrderMutationKind,
) => {
    if (scope.businessId === null) return;

    const targets = invalidationTargets[mutation];
    const invalidations: Promise<void>[] = [];

    if (targets.list) {
        invalidations.push(queryClient.invalidateQueries({
            queryKey: orderQueryKeys.listPrefix(scope.userId, scope.businessId),
        }));
    }

    if (orderId !== undefined) {
        if (targets.detail) {
            invalidations.push(queryClient.invalidateQueries({
                queryKey: orderQueryKeys.detail(scope.userId, scope.businessId, orderId),
                exact: true,
            }));
        }
        if (targets.statusHistory) {
            invalidations.push(queryClient.invalidateQueries({
                queryKey: orderQueryKeys.statusHistory(scope.userId, scope.businessId, orderId),
                exact: true,
            }));
        }
        if (targets.consumption) {
            invalidations.push(queryClient.invalidateQueries({
                queryKey: orderQueryKeys.consumption(scope.userId, scope.businessId, orderId),
                exact: true,
            }));
        }
        if (targets.refund) {
            invalidations.push(queryClient.invalidateQueries({
                queryKey: orderQueryKeys.refund(scope.userId, scope.businessId, orderId),
                exact: true,
            }));
        }
    }

    await Promise.all(invalidations);
};
