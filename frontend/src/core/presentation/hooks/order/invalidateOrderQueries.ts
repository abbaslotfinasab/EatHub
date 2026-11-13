import type {QueryClient} from "@tanstack/react-query";

import {orderQueryKeys} from "./orderQueryKeys";

export interface OrderQueryScope {
    userId: number | null;
    businessId: number | null;
}

export interface OrderQueryInvalidationTargets {
    list?: boolean;
    detail?: boolean;
    statusHistory?: boolean;
    consumption?: boolean;
    refund?: boolean;
}

export const invalidateOrderQueries = async (
    queryClient: QueryClient,
    scope: OrderQueryScope,
    orderId: string | undefined,
    targets: OrderQueryInvalidationTargets,
) => {
    if (scope.businessId === null) return;

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
