import { isAxiosError } from "axios";
import type { RecipeRepository } from "../../domain/repositories/product/RecipeRepository";
import type { Recipe } from "../../domain/entities/product/Recipe";
import type { RecipeComponents } from "../../domain/entities/product/RecipeComponents";
import type { RecipeResult } from "../../domain/entities/product/RecipeResult";
import type { RecipeFilters } from "../../domain/objects/filters/RecipeFilters";
import { apiClient } from "../http/http-client";

interface ApiRecipeLine {
    id: number;
    ingredient_id: number;
    ingredient_name: string;
    material_type: "raw" | "compound";
    quantity: string;
    unit: string;
    notes: string | null;
    is_primary?: boolean;
}

interface ApiRecipe {
    id: number;
    name: string;
    code: string | null;
    type: "preparation" | "production";
    description: string | null;
    is_active: boolean;
    inputs: ApiRecipeLine[];
    outputs: ApiRecipeLine[];
    created_at: string;
    updated_at: string;
}

interface ApiRecipePage {
    count: number;
    page: number;
    page_size: number;
    results: ApiRecipe[];
}

const fromApi = (recipe: ApiRecipe): RecipeResult => ({
    recipe: {
        id: String(recipe.id),
        name: recipe.name,
        description: recipe.description,
        createdAt: recipe.created_at,
        updatedAt: recipe.updated_at,
    },
    ingredients: recipe.inputs.map((line) => ({
        id: String(line.id),
        recipeId: String(recipe.id),
        componentType: "ingredient",
        ingredientId: String(line.ingredient_id),
        ingredientName: line.ingredient_name,
        materialType: line.material_type,
        materialId: null,
        quantity: String(line.quantity),
        unit: line.unit,
        notes: line.notes ?? null,
        isPrimary: line.is_primary ?? false,
        substituteIngredientId: null,
        substituteMaterialId: null,
        createdAt: recipe.created_at,
        updatedAt: recipe.updated_at,
    })),
    outputs: recipe.outputs.map((line) => ({
        id: String(line.id),
        recipeId: String(recipe.id),
        componentType: "ingredient",
        ingredientId: String(line.ingredient_id),
        ingredientName: line.ingredient_name,
        materialType: line.material_type,
        materialId: null,
        quantity: String(line.quantity),
        unit: line.unit,
        notes: line.notes ?? null,
        isPrimary: line.is_primary ?? false,
        substituteIngredientId: null,
        substituteMaterialId: null,
        createdAt: recipe.created_at,
        updatedAt: recipe.updated_at,
    })),
});

const lineToApi = (line: Partial<RecipeComponents>, output = false) => {
    if (!line.ingredientId || line.materialId) {
        throw new Error("Recipes can currently contain Inventory ingredients only.");
    }
    if (!line.unit) {
        throw new Error("Each recipe ingredient requires a unit.");
    }
    return {
        ingredient_id: Number(line.ingredientId),
        quantity: line.quantity,
        unit: line.unit,
        notes: line.notes ?? null,
        ...(output ? { is_primary: line.isPrimary ?? false } : {}),
    };
};

export class RecipeRepositoryImpl implements RecipeRepository {
    async create(
        recipe: Omit<Recipe, "id" | "createdAt" | "updatedAt">,
        ingredients: Omit<RecipeComponents, "id" | "createdAt" | "updatedAt">[],
        outputs: Omit<RecipeComponents, "id" | "createdAt" | "updatedAt">[],
    ): Promise<RecipeResult> {
        const { data } = await apiClient.post<ApiRecipe>("/inventory/recipes/", {
            name: recipe.name?.trim(),
            description: recipe.description ?? null,
            type: "preparation",
            inputs: ingredients.map((line) => lineToApi(line)),
            outputs: outputs.map((line) => lineToApi(line, true)),
        });
        return fromApi(data);
    }

    async update(
        recipeId: string,
        recipeData: Partial<Recipe>,
        ingredients: Omit<RecipeComponents, "id" | "createdAt" | "updatedAt" | "componentType">[],
        outputs: Omit<RecipeComponents, "id" | "createdAt" | "updatedAt" | "componentType">[],
    ): Promise<RecipeResult> {
        const { data } = await apiClient.patch<ApiRecipe>(`/inventory/recipes/${recipeId}/`, {
            ...(recipeData.name !== undefined ? { name: recipeData.name } : {}),
            ...(recipeData.description !== undefined ? { description: recipeData.description } : {}),
            inputs: ingredients.map((line) => lineToApi(line)),
            outputs: outputs.map((line) => lineToApi(line, true)),
        });
        return fromApi(data);
    }

    async findById(id: string): Promise<RecipeResult | null> {
        try {
            const { data } = await apiClient.get<ApiRecipe>(`/inventory/recipes/${id}/`);
            return fromApi(data);
        } catch (error) {
            if (isAxiosError(error) && error.response?.status === 404) return null;
            throw error;
        }
    }

    async findAll(filters?: RecipeFilters): Promise<RecipeResult[]> {
        const pageSize = 100;
        const recipes: ApiRecipe[] = [];
        let page = 1;

        while (true) {
            const { data } = await apiClient.get<ApiRecipePage>("/inventory/recipes/", {
                params: {
                    page,
                    page_size: pageSize,
                    ...(filters?.search ? { search: filters.search } : {}),
                },
            });
            recipes.push(...data.results);

            // Stop on a short or empty page, or when the server-reported total
            // has been collected. This avoids requesting an unnecessary page.
            if (
                data.results.length === 0
                || data.results.length < pageSize
                || recipes.length >= data.count
            ) {
                break;
            }
            page += 1;
        }

        return recipes.map(fromApi);
    }

    async delete(id: string): Promise<void> {
        await apiClient.patch(`/inventory/recipes/${id}/`, { is_active: false });
    }
}
