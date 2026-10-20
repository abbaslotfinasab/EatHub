import type {
    StockBalance,
    StockBalancePage,
} from "../../domain/entities/inventory/StockBalance";
import type {
    StockBalanceDTO,
    StockBalancePageDTO,
} from "../dtos/inventory/StockBalanceDTO";

const toStockBalance = (dto: StockBalanceDTO): StockBalance => ({
    id: dto.id,
    ingredientId: dto.ingredient_id,
    ingredientName: dto.ingredient_name,
    warehouseId: dto.warehouse_id,
    warehouseName: dto.warehouse_name,
    quantity: dto.quantity,
    unit: dto.unit,
    averageCost: dto.average_cost,
});

export const stockBalanceMapper = {
    toDomain(dto: StockBalancePageDTO): StockBalancePage {
        return {
            count: dto.count,
            page: dto.page,
            pageSize: dto.page_size,
            results: dto.results.map(toStockBalance),
        };
    },
};
