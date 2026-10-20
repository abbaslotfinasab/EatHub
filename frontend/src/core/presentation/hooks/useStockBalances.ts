import { useQuery } from "@tanstack/react-query";
import type { StockBalanceFilters } from "../../domain/entities/inventory/StockBalance";
import { listStockBalancesUseCase } from "../../data/di/stockBalance.container";
import { useAuthStore } from "../store/auth.store";

export const useStockBalances = (filters: StockBalanceFilters) => {
    const accessToken = useAuthStore((state) => state.accessToken);
    const userId = useAuthStore((state) => state.me?.id ?? null);
    const businessId = useAuthStore(
        (state) => state.me?.active_business?.id ?? null,
    );

    return useQuery({
        queryKey: ["inventory-stock-balances", userId, businessId, filters],
        queryFn: () => listStockBalancesUseCase.execute(filters),
        enabled: Boolean(accessToken && userId !== null && businessId !== null),
        placeholderData: (previousData, previousQuery) => {
            if (!previousData || !previousQuery) return undefined;

            const previousKey = previousQuery.queryKey;
            const previousFilters = previousKey[3] as StockBalanceFilters | undefined;
            const sameResultSet =
                previousKey[0] === "inventory-stock-balances" &&
                previousKey[1] === userId &&
                previousKey[2] === businessId &&
                previousFilters?.pageSize === filters.pageSize &&
                previousFilters?.ingredientId === filters.ingredientId &&
                previousFilters?.warehouseId === filters.warehouseId;

            // Keep the page count while changing pages, but never carry rows
            // across a user, business, or filter change.
            return sameResultSet ? previousData : undefined;
        },
    });
};
