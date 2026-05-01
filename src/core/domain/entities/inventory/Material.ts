// core/domain/entities/Recipe.ts

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


export interface Material {
    id?: string;
    name: string;
    description?: string | null;
    currentStock: number;
    reorderLevel: number;      // هشدار موجودی
    reorderQuantity: number;   // مقدار پیشنهادی برای خرید مجدد
    unit: UnitType;
    costPrice?: number;
    createdAt?: string;
    updatedAt?: string;
}
