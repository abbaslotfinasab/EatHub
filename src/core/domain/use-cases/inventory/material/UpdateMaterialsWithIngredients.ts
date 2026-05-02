// application/use-cases/material/UpdateMaterialWithIngredients.ts
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';
import type { Material } from '../../../entities/inventory/Material';
import type {MaterialIngredientRepository} from "../../../repositories/inventory/MaterialIngredientRepository.ts";

export interface MaterialIngredientInput {
    ingredientId: string;
    quantity: number;
    unit?: string;
}

export interface UpdateMaterialWithIngredientsCommand {
    materialId: string;
    materialData: Partial<Omit<Material, 'id'>>;
    ingredients: MaterialIngredientInput[];
}

export class UpdateMaterialWithIngredients {
    constructor(
        private readonly materialIngredientRepository: MaterialIngredientRepository,
        private readonly materialRepository: MaterialRepository
    ) {}

    async execute(command: UpdateMaterialWithIngredientsCommand): Promise<void> {
        const { materialId, materialData, ingredients } = command;

        // اعتبارسنجی سطحی (وجود ماده)
        const existing = await this.materialRepository.findById(materialId);
        if (!existing) throw new Error(`Material with ID "${materialId}" not found`);

        // ارسال یک درخواست PUT یا PATCH به endpoint ترکیبی
        await this.materialIngredientRepository.updateWithIngredients(materialId, {
            ...materialData,
            ingredients,
        });
    }
}