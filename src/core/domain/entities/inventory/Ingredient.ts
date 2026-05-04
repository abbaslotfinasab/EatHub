// src/core/domain/inventory/entities/Ingredient.ts

// unit.ts
export const Unit = {
    KG: 'kg',
    G: 'g',
    L: 'l',
    ML: 'ml',
    PIECE: 'pc',
    PACK: 'pk',
} as const;

export type UnitType = typeof Unit[keyof typeof Unit];

export const UnitLabel: Record<UnitType, string> = {
    [Unit.KG]: 'کیلوگرم',
    [Unit.G]: 'گرم',
    [Unit.L]: 'لیتر',
    [Unit.ML]: 'میلی‌لیتر',
    [Unit.PIECE]: 'عدد',
    [Unit.PACK]: 'بسته',
};

export interface Ingredient {
    id?: string;
    name: string;
    unit: UnitType;
    currentStock: number;
    reorderLevel: number;      // هشدار موجودی
    reorderQuantity?: number;   // مقدار پیشنهادی برای خرید مجدد
    costPrice: number;         // قیمت تمام‌شده فعلی (به ازای هر واحد)
    sku?: string | null;        // کد انبار (اختیاری)
    isActive: boolean;
    categoryId?: string | null;
    complete: boolean;         // آماده با نبمه آماده
    createdAt?: string;         // ISO
    updatedAt?: string;
}
