
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


export interface MaterialIngredient {
    id: string;
    materialId: string;
    ingredientId: string;
    quantity: number;      // مقدار مصرف برای yield مشخص شده در Recipe
    // اختیاری: اگر واحد ماده با واحد مصرف متفاوت است، می‌توان unitOverride داشت
    unit?: UnitType;
    // برای جایگزینی مواد
    substituteIngredientId?: string | null;
}
