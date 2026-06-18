export interface PurchaseOrderItem {
    id: string;
    purchaseOrderId: string;         // ارجاع به سر فاکتور
    ingredientId: string;            // کدام ماده اولیه خریداری شده
    quantity: number;                // مقدار خریداری شده (بر حسب واحد ماده)
    unitPrice: number;               // قیمت واحد (به ازای هر واحد ماده)
    totalPrice: number;              //= quantity * unitPrice
    createdAt: string;
    updatedAt: string;
}