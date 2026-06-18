// core/domain/entities/sales/Reservation.ts

export interface Reservation {
    id?: string;
    customerName: string;
    customerPhone: string;
    customerEmail?: string | null;   // اختیاری
    tableId: string;                 // ارجاع به میز
    reservationDate: string;         // تاریخ رزرو (ISO)
    reservationTime: string;         // ساعت رزرو (مثلاً "20:00")
    partySize: number;               // تعداد نفرات
    statusId?: string;
    specialRequests?: string | null; // درخواست‌های ویژه (مثلاً جای کنار پنجره)
    orderId?: string | null;         // اگر رزرو به سفارش غذا هم متصل بشه (اختیاری)
    createdAt?: string;
    updatedAt?: string;
}