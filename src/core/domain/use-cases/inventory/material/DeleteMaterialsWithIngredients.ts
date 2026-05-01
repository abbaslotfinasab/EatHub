// core/application/use-cases/material/DeleteMaterialWithIngredients.ts
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';
import type { MaterialIngredientRepository } from '../../../repositories/inventory/MaterialIngredientRepository';

export class DeleteMaterialWithIngredients {
    constructor(
        private readonly materialRepository: MaterialRepository,
        private readonly materialIngredientRepository: MaterialIngredientRepository,
    ) {}

    async execute(materialId: string): Promise<void> {
        // 1. بررسی وجود ماده
        const material = await this.materialRepository.findById(materialId);
        if (!material || !material.id) {
            throw new Error('Material not found');
        }

        // 2. بررسی اینکه آیا این ماده در جای دیگر به عنوان ماده مصرفی (Ingredient) استفاده شده است؟
        const isUsedAsIngredient = await this.materialIngredientRepository.findByIngredientId(material.id);
        if (isUsedAsIngredient.length > 0) {
            throw new Error('Cannot delete material because it is used as an ingredient in other materials');
        }

        // 3. دریافت روابط (مواد مصرفی این ماده)
        const relations = await this.materialIngredientRepository.findByMaterialId(material.id);

        // 4. حذف روابط (اگر متد حذف دسته‌جمعی وجود دارد، استفاده شود)
        if (relations.length > 0) {
            // روش 1: حذف تک‌تک (کند)
            for (const rel of relations) {
                await this.materialIngredientRepository.delete(rel.id);
            }
            // روش 2: در صورت وجود متد deleteByMaterialId
            // await this.materialIngredientRepository.deleteByMaterialId(material.id);
        }

        // 5. حذف خود ماده
        await this.materialRepository.delete(material.id);
    }
}