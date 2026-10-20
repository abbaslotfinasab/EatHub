// src/presentation/providers/QueryProvider.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useEffect, useRef } from 'react';
import { useAuthStore } from '../store/auth.store';

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
    const businessId = useAuthStore(
        (state) => state.me?.active_business?.id ?? null,
    );
    const previousIdentity = useRef<{
        userId: number | null;
        businessId: number | null;
    } | null>(null);

    useEffect(() => {
        const previous = previousIdentity.current;
        if (
            previous &&
            (previous.userId !== userId || previous.businessId !== businessId)
        ) {
            if (previous.userId !== null && previous.businessId !== null) {
                queryClient.removeQueries({
                    queryKey: [
                        'inventory-stock-balances',
                        previous.userId,
                        previous.businessId,
                    ],
                });
            } else if (userId === null || businessId === null) {
                // Also clear any balance entries when leaving an authenticated context.
                queryClient.removeQueries({
                    queryKey: ['inventory-stock-balances'],
                });
            }
        }
        previousIdentity.current = { userId, businessId };
    }, [userId, businessId]);

    return (
        <QueryClientProvider client={queryClient}>
            {children}
        </QueryClientProvider>
    );
};
