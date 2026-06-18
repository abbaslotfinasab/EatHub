// core/domain/entities/sales/MenuCategory.ts
export interface Menu {
    id: string;
    name: string;                // مثلاً "نوشیدنی‌ها"، "پیش‌غذا" یا اسامی خاص برای اسم منو
    category: string;                // مثلاً "نوشیدنی‌ها"، "پیش‌غذا"
    description?: string | null ;
    sortOrder: number;           // ترتیب نمایش در منو
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
}


