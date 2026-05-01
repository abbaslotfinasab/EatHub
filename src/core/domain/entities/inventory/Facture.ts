


// domain/entities/PurchaseOrderStatus.ts
export const PurchaseOrderStatus = {
    DRAFT: 'draft',
    ORDERED: 'ordered',
    PARTIALLY_RECEIVED: 'partially_received',
    RECEIVED: 'received',
    CANCELLED: 'cancelled',
} as const;

export type PurchaseOrderStatusType = typeof PurchaseOrderStatus[keyof typeof PurchaseOrderStatus];

// همچنین می‌توانی یک آبجکت برای برچسب‌های فارسی هم داشته باشی
export const PurchaseOrderStatusLabel: Record<PurchaseOrderStatusType, string> = {
    [PurchaseOrderStatus.DRAFT]: 'پیش‌نویس',
    [PurchaseOrderStatus.ORDERED]: 'سفارش داده شده',
    [PurchaseOrderStatus.PARTIALLY_RECEIVED]: 'دریافت جزئی',
    [PurchaseOrderStatus.RECEIVED]: 'دریافت کامل',
    [PurchaseOrderStatus.CANCELLED]: 'لغو شده',
};

export interface PurchaseOrder {
    id: string;
    supplierId: string;              // ارجاع به تأمین‌کننده
    orderDate: string;               // تاریخ ثبت سفارش (ISO)
    expectedDeliveryDate: string | null; // تاریخ تحویل مورد انتظار
    receivedDate: string | null;     // تاریخ دریافت کامل (واقعی)
    status?: PurchaseOrderStatusType;
    totalAmount: number;             // جمع کل فاکتور (محاسبه شده از جزییات)
    invoiceNumber: string | null;    // شماره فاکتور مرجع از طرف تأمین‌کننده
    notes: string | null;            // توضیحات اضافی
    createdAt: string;
    updatedAt: string;
}


// domain/entities/PurchaseOrderItem.ts
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