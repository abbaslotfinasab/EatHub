// core/domain/entities/sales/Cart.ts

export const CartStatus = {
    ACTIVE: 'active',           // در حال استفاده
    CONVERTED: 'converted',     // تبدیل به سفارش شده
    ABANDONED: 'abandoned',     // رها شده
} as const;

export type CartStatusType = typeof CartStatus[keyof typeof CartStatus];

export interface Cart {
    id: string;
    customerId?: string;        // شناسه کاربر عضو (در صورت لاگین)
    sessionId?: string;         // شناسه نشست (برای مهمان‌ها)
    totalAmount?: number;        // جمع کل (قابل محاسبه از آیتم‌ها)
    status: CartStatusType;
    expiresAt?: string;         // زمان انقضا (مثلاً ۲۴ ساعت بعد از آخرین فعالیت)
    createdAt: string;
    updatedAt: string;
}