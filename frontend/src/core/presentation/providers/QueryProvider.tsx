// src/presentation/providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { useAuthStore } from "../store/auth.store";
import { useBusinessContextStore } from "../store/business-context.store";

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
            // Tenant-scoped query keys are not yet universal across the application.
            // Cancel in-flight work and clear the entire cache to prevent any
            // previous-business data from being observed after a context switch.
            void queryClient.cancelQueries();
            queryClient.clear();
        }
        previousIdentity.current = { userId, businessId };
    }, [userId, businessId]);

    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
};
