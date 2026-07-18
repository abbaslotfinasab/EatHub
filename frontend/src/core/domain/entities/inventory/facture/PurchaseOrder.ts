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
    id?: string;
    supplierId?: string;              // ارجاع به تأمین‌کننده
    supplierName: string | null;              // ارجاع به تأمین‌کننده
    supplierNumber: string | null;              // ارجاع به تأمین‌کننده
    type?: string;
    status?: PurchaseOrderStatusType;
    subtotal: number | null;             // جمع قیمت اقلام (بدون تخفیف)
    discount: number | null;             // مبلغ تخفیف
    tax: number | null;                  // مالیات (در صورت وجود)
    totalAmount: number;          // مبلغ نهایی = subtotal - discount + tax
    invoiceNumber: string | null;    // شماره فاکتور مرجع از طرف تأمین‌کننده
    notes: string | null;            // توضیحات اضافی
    createdAt?: string;
    updatedAt?: string;
}
