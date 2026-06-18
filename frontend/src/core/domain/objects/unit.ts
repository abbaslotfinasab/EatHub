// src/core/objects/unit.ts

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