
export interface MaterialIngredient {
    id?: string;
    materialId?: string;
    ingredientId?: string;
    quantity?: number;      // مقدار مصرف برای yield مشخص شده در Recipe
    // اختیاری: اگر واحد ماده با واحد مصرف متفاوت است، می‌توان unitOverride داشت
    unitId?: string;
    // برای جایگزینی مواد
    substituteIngredientId?: string | null;
}
