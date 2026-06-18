// core/domain/entities/Recipe.ts


export interface Material {
    id?: string;
    name: string;
    categoryId?: string | null;
    description?: string | null;
    currentStock: number;
    reorderLevel: number;      // هشدار موجودی
    reorderQuantity: number;   // مقدار پیشنهادی برای خرید مجدد
    unitId: string;
    costPrice?: number;
    createdAt?: string;
    updatedAt?: string;
}
