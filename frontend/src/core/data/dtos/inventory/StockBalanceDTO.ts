export interface StockBalanceDTO {
    id: number;
    ingredient_id: number;
    ingredient_name: string;
    material_type: "raw" | "compound";
    warehouse_id: number;
    warehouse_name: string;
    quantity: string;
    unit: "kg" | "g" | "l" | "ml" | "pc" | "pk";
    average_cost: string;
}

export interface StockBalancePageDTO {
    count: number;
    page: number;
    page_size: number;
    results: StockBalanceDTO[];
}
