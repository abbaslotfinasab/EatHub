export interface OrderConsumptionRequirement {
    requirementId: number;
    orderItemId: number;
    menuItemName: string;
    ingredientId: number;
    ingredientName: string;
    standardQuantity: string;
    actualQuantity: string;
    unit: string;
    hasActualRecord: boolean;
}

export interface OrderConsumptionRequirements {
    orderId: number;
    requirements: OrderConsumptionRequirement[];
}

export interface RecordOrderConsumptionInput {
    orderId: string;
    idempotencyKey: string;
    lines: Array<{
        requirementId: number;
        quantity: string;
        unit: string;
    }>;
}

export interface RecordOrderConsumptionResult {
    id: number;
    orderId: number;
    idempotencyKey: string;
    createdAt: string;
    inventoryOperationId: number | null;
    lines: Array<{
        requirementId: number;
        orderItemId: number;
        ingredientId: number;
        actualQuantity: string;
        unit: string;
        movementId: number | null;
    }>;
}
