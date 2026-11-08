// src/presentation/providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useAuthStore } from "../store/auth.store";
import { useBusinessContextStore } from "../store/business-context.store";
import { orderQueryKeys } from "../hooks/order/orderQueryKeys";

const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: false,
            refetchOnWindowFocus: false,
        },
    },
});

export const QueryProvider = ({ children }: { children: React.ReactNode }) => {
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useBusinessContextStore((state) => state.selectedBusinessId);
    const previousIdentity = useRef<{ userId: number | null; businessId: number | null } | null>(null);

    useEffect(() => {
        const previous = previousIdentity.current;
        if (previous && (previous.userId !== userId || previous.businessId !== businessId)) {
            // Cancel first so late responses cannot repopulate the previous tenant's cache.
            void queryClient.cancelQueries();
            if (previous.userId !== null && previous.businessId !== null) {
                queryClient.removeQueries({
                    queryKey: orderQueryKeys.business(previous.userId, previous.businessId),
                });
                queryClient.removeQueries({
                    queryKey: ["inventory-stock-balances", previous.userId, previous.businessId],
                });
            }
            if (userId === null) {
                queryClient.clear();
            }
        }
        previousIdentity.current = { userId, businessId };
    }, [userId, businessId]);

    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
};
