// core/domain/entities/sales/OrderItem.ts
export interface OrderItem {
    id: string;
    orderId: string;
    menuItemId: string;
    menuItemName?: string;        // نام آیتم منو (برای نمایش/ گزارش)
    quantity: number;
    unitPrice?: number;           // قیمت واحد در زمان سفارش (قفل شود)
    totalPrice?: number;          // = quantity * unitPrice
    notes?: string | null | undefined;              // توضیحات برای آشپز (مثل "کم نمک")
    createdAt?: string;
    updatedAt?: string;
}