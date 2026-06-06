// core/domain/entities/sales/Table.ts

export interface Table {
    id?: string;
    number: string;          // شماره میز (مثلاً "12" یا "A3")
    capacity: number;        // ظرفیت (تعداد نفر)
    isAvailable?: boolean;    // آیا الان آزاد است؟ (برای رزروهای همان روز)
    section?: string | null; // سالن یا بخش (مثلاً "تراس", "سالن اصلی")
    createdAt?: string;
    updatedAt?: string;
}