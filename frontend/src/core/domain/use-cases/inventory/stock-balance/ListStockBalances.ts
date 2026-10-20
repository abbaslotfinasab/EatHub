import type {
    StockBalanceFilters,
    StockBalancePage,
} from "../../../entities/inventory/StockBalance";
import type { StockBalanceRepository } from "../../../repositories/inventory/StockBalanceRepository";

export class ListStockBalances {
    constructor(private readonly repository: StockBalanceRepository) {}

    execute(filters: StockBalanceFilters): Promise<StockBalancePage> {
        return this.repository.list(filters);
    }
}
