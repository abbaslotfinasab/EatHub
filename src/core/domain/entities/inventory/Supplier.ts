// core/domain/entities/Supplier.ts

// شرایط پرداخت به صورت ثابت (مشابه Unit)
export const PaymentTerms = {
    CASH: 'cash',           // نقدی
    NET_15: 'net_15',       // 15 روزه
    NET_30: 'net_30',       // 30 روزه
    NET_45: 'net_45',       // 45 روزه
} as const;

export type PaymentTermsType = typeof PaymentTerms[keyof typeof PaymentTerms];

export interface Supplier {
    id?: string;
    name: string;                    // نام تأمین‌کننده
    contactPerson?: string | null;    // شخص تماس
    phone: string;                   // تلفن
    email?: string | null;            // ایمیل
    address?: string | null;          // آدرس
    taxNumber?: string | null;        // شماره مالیاتی
    paymentTerms?: PaymentTermsType;  // شرایط پرداخت
    notes?: string | null;            // توضیحات اضافی
    isActive: boolean;               // فعال/غیرفعال
    createdAt?: string;               // ISO
    updatedAt?: string;
}