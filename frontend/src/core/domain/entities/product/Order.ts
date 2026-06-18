// core/domain/entities/sales/Order.ts


export const OrderStatus = {
    PENDING: 'pending',           // ثبت شده، در انتظار پرداخت یا تأیید
    CONFIRMED: 'confirmed',       // تأیید شده (پرداخت انجام شده یا دستور پخت صادر شده)
    PREPARING: 'preparing',       // در حال آماده‌سازی (آشپزخانه)
    READY: 'ready',               // آماده تحویل به مشتری
    COMPLETED: 'completed',       // تحویل شده و بسته شده
    CANCELLED: 'cancelled',       // لغو شده توسط مشتری یا رستوران
    FAILED: 'failed',             // پرداخت ناموفق
} as const;

export type OrderStatusType = typeof OrderStatus[keyof typeof OrderStatus];

export interface Order {
    id: string;
    customerId?: string;          // اگر کاربر احراز هویت شده
    customerName: string;         // نام مشتری (برای مهمان یا پرسنل ثبت کننده)
    customerPhone?: string | null;
    tableId?: string | null;      // اگر سفارش برای میز است
    orderType: 'dine_in' | 'takeaway' | 'delivery';
    status: OrderStatusType;
    subtotal: number;             // جمع قیمت اقلام (بدون تخفیف)
    discount: number;             // مبلغ تخفیف
    tax: number;                  // مالیات (در صورت وجود)
    totalAmount: number;          // مبلغ نهایی = subtotal - discount + tax
    // paymentMethod: PaymentMethodType;
    paymentStatus?: 'pending' | 'paid' | 'failed' | 'refunded';
    notes?: string | null;               // توضیحات عمومی سفارش
    createdAt?: string;
    updatedAt?: string;
}

