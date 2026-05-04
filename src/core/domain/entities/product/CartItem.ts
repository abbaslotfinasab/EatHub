// core/domain/entities/sales/CartItem.ts
export interface CartItem {
    id: string;
    cartId: string;             // ارجاع به سبد خرید
    menuItemId: string;         // محصول (آیتم منو)
    quantity: number;           // تعداد
    unitPrice: number;          // قیمت واحد در زمان اضافه شدن (قفل شود)
    totalPrice: number;         // = quantity * unitPrice
    notes?: string;             // توضیحات اضافی (مثل "بدون پیاز")
    createdAt: string;
    updatedAt: string;
}