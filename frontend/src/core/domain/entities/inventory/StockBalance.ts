export type StockUnit = "kg" | "g" | "l" | "ml" | "pc" | "pk";

export interface StockBalance {
    id: number;
    ingredientId: number;
    ingredientName: string;
    warehouseId: number;
    warehouseName: string;
    quantity: string;
    unit: StockUnit;
    averageCost: string;
}

export interface StockBalancePage {
    count: number;
    page: number;
    pageSize: number;
    results: StockBalance[];
}

export interface StockBalanceFilters {
    page: number;
    pageSize: number;
    ingredientId?: number;
    warehouseId?: number;
}
