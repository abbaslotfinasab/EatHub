// core/domain/entities/sales/MenuCategory.ts
export interface Menu {
    id: string;
    name: string;                // مثلاً "نوشیدنی‌ها"، "پیش‌غذا" یا اسامی خاص برای اسم منو
    category: string;                // مثلاً "نوشیدنی‌ها"، "پیش‌غذا"
    description: string | null;
    sortOrder: number;           // ترتیب نمایش در منو
    isActive: boolean;
    createdAt: string;
    updatedAt: string;
}


// core/domain/entities/sales/MenuItem.ts
export interface MenuItem {
    id: string;
    name: string;
    description: string | null;
    price: number;               // قیمت فروش (تومان/ریال)
    imageUrl: string | null;
    menuId: string;          // ارجاع به Menu
    isAvailable: boolean;        // موجود در منو (می‌تواند به موجودی انبار وابسته باشد)
    recipeId: string | null;     // ارجاع به Recipe (اختیاری – اگر غذا نیاز به مواد اولیه از انبار دارد)
    createdAt: string;
    updatedAt: string;
}