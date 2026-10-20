import type {
    StockBalanceFilters,
    StockBalancePage,
} from "../../entities/inventory/StockBalance";

export interface StockBalanceRepository {
    list(filters: StockBalanceFilters): Promise<StockBalancePage>;
}
