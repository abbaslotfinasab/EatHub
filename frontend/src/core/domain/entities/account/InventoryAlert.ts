export interface InventoryAlert {
    id: string;

    ingredientName: string;

    currentStock: number;

    minimumStock: number;

    unit: string;

    severity:
        | "critical"
        | "warning"
        | "low";
}