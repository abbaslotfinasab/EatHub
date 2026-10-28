import { apiClient } from "../http/http-client";
import type { StockBalanceFilters } from "../../domain/entities/inventory/StockBalance";
import type { StockBalancePageDTO } from "../dtos/inventory/StockBalanceDTO";

export class StockBalanceRemoteDataSource {
    async list(filters: StockBalanceFilters): Promise<StockBalancePageDTO> {
        const params: Record<string, string | number> = {
            page: filters.page,
            page_size: filters.pageSize,
        };
        if (filters.ingredientId !== undefined) {
            params.ingredient_id = filters.ingredientId;
        }
        if (filters.warehouseId !== undefined) {
            params.warehouse_id = filters.warehouseId;
        }
        if (filters.materialType !== undefined) params.material_type = filters.materialType;
        if (filters.search?.trim()) params.search = filters.search.trim();
        const response = await apiClient.get<StockBalancePageDTO>(
            "/inventory/balances/",
            { params },
        );
        return response.data;
    }
}
