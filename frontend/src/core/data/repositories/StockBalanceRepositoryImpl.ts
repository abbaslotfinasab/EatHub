import type {
    StockBalanceFilters,
    StockBalancePage,
} from "../../domain/entities/inventory/StockBalance";
import type { StockBalanceRepository } from "../../domain/repositories/inventory/StockBalanceRepository";
import type { StockBalanceRemoteDataSource } from "../datasources/StockBalanceRemoteDataSource";
import { stockBalanceMapper } from "../mappers/stockBalanceMapper";

export class StockBalanceRepositoryImpl implements StockBalanceRepository {
    constructor(private readonly remote: StockBalanceRemoteDataSource) {}

    async list(filters: StockBalanceFilters): Promise<StockBalancePage> {
        const dto = await this.remote.list(filters);
        return stockBalanceMapper.toDomain(dto);
    }
}
