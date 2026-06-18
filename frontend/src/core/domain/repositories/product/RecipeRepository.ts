// core/domain/repositories/sales/RecipeRepository.ts
import type { Recipe } from '../../entities/product/Recipe';
import type { RecipeComponents } from '../../entities/product/RecipeComponents.ts';
import type {RecipeResult} from "../../entities/product/RecipeResult.ts";
import type {RecipeFilters} from "../../objects/filters/RecipeFilters.ts";



export interface RecipeRepository {

    // ذخیره یک رسپی به همراه لیست مواد مصرفی (atomic in backend)
    create(
        recipe: Omit<Recipe, 'id' | 'createdAt' | 'updatedAt'>,
        // فقط فیلدهای ضروری بدون id, recipeId, createdAt, updatedAt
        ingredients: Omit<RecipeComponents, 'id' | 'createdAt' | 'updatedAt'>[]
    ): Promise<RecipeResult>;
    // پیدا کردن رسپی با شناسه (بدون ingredients)
    findById(id: string): Promise<RecipeResult | null>;

    // (اختیاری) دریافت تمام رسپی‌ها (بدون جزئیات مواد)
    findAll(filters?: RecipeFilters): Promise<RecipeResult[]>;


    // به‌روزرسانی رسپی و جایگزینی کامل مواد مصرفی (delete old + insert new)
    update(recipeId: string, recipeData: Partial<Recipe>, ingredients: Omit<RecipeComponents, 'id' | 'createdAt' | 'updatedAt' | 'componentType' >[]): Promise<RecipeResult>;


    delete(id: string): Promise<void>;


}