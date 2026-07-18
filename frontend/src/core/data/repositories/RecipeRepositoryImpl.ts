// src/core/data/repositories/RecipeRepositoryImpl.ts

import type { RecipeRepository } from "../../domain/repositories/product/RecipeRepository";
import type { Recipe } from "../../domain/entities/product/Recipe";
import type { RecipeComponents } from "../../domain/entities/product/RecipeComponents";
import type { RecipeResult } from "../../domain/entities/product/RecipeResult";
import type { RecipeFilters } from "../../domain/objects/filters/RecipeFilters";
import { apiClient } from "../http/http-client";
import {isAxiosError} from "axios";
import {mockIngredients, mockRecipes} from "../dtos/recipe/recipe.ts";

export class RecipeRepositoryImpl implements RecipeRepository {

    // ایجاد رسپی جدید به همراه مواد مصرفی
    async create(
        recipe: Omit<Recipe, "id" | "createdAt" | "updatedAt">,
        ingredients: Omit<RecipeComponents, "id" | "createdAt" | "updatedAt">[]
    ): Promise<RecipeResult> {
        const response = await apiClient.post('/recipes/with-ingredients', {
            recipe,
            ingredients,
        });
        return response.data;
    }

    // به‌روزرسانی رسپی و جایگزینی کامل مواد مصرفی
    async update(
        recipeId: string,
        recipeData: Partial<Recipe>,
        ingredients: Omit<RecipeComponents, "id" | "createdAt" | "updatedAt" | "componentType">[]
    ): Promise<RecipeResult> {
        const response = await apiClient.put(`/recipes/${recipeId}/with-ingredients`, {
            recipeData,
            ingredients,
        });
        return response.data;
    }

    // دریافت یک رسپی به همراه مواد (با شناسه)
    async findById(id: string): Promise<RecipeResult | null> {
        try {
            const response = await apiClient.get(`/recipes/${id}/with-ingredients`);
            return response.data;
        }  catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) {
                return null;
            }
            throw error;
        }
    }

    // دریافت لیست رسپی‌ها با قابلیت فیلتر
    async findAll(filters?: RecipeFilters): Promise<RecipeResult[]> {
        // ساخت query string از فیلترها
        // const params = new URLSearchParams();
        // if (filters) {
        //     Object.entries(filters).forEach(([key, value]) => {
        //         if (value !== undefined && value !== null) {
        //             params.append(key, String(value));
        //         }
        //     });
        // }
        // const queryString = params.toString();
        // const url = queryString ? `/recipes?${queryString}` : '/recipes';
        // const response = await apiClient.get(url);
        // return response.data; // فرض بر این است که بک‌اند آرایه‌ای از RecipeResult برمی‌گرداند


        let filteredRecipes = [...mockRecipes];
        if (filters?.search) {
            const term = filters.search.toLowerCase();
            filteredRecipes = filteredRecipes.filter(r => r.name?.toLowerCase().includes(term));
        }

        // اطمینان از وجود id و تبدیل به آرایه نتیجه
        const results: RecipeResult[] = filteredRecipes
            .filter((recipe): recipe is Recipe & { id: string } => !!recipe.id) // فقط رسپی‌هایی که id دارند
            .map(recipe => ({
                recipe,
                ingredients: mockIngredients[recipe.id] || [], // حالا recipe.id حتماً string است
            }));
        return results;

    }

    // حذف رسپی (به همراه مواد وابسته در بک‌اند)
    async delete(id: string): Promise<void> {
        await apiClient.delete(`/recipes/${id}`);
    }
}