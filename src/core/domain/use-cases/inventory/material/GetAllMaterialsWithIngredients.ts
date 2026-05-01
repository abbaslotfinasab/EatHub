// core/application/use-cases/material/GetAllMaterialsWithIngredients.ts
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';
import type { MaterialIngredientRepository } from '../../../repositories/inventory/MaterialIngredientRepository';
import type { IngredientRepository } from '../../../repositories/inventory/IngredientRepository';
import type { Material } from '../../../entities/inventory/Material';
import type { MaterialIngredient } from '../../../entities/inventory/MaterialIngredient';

export interface MaterialWithIngredients {
    material: Material;
    ingredients: {
        id: string;
        name: string;
        quantity: number;
        category: string;
        unit: string;
        costPrice?: number;
        currentStock: number;
    }[];
}

export class GetAllMaterialsWithIngredients {
    constructor(
        private readonly materialRepository: MaterialRepository,
        private readonly materialIngredientRepository: MaterialIngredientRepository,
        private readonly ingredientRepository: IngredientRepository, // 🔹 اضافه شد
    ) {}

    async execute(): Promise<MaterialWithIngredients[]> {
        const materials = await this.materialRepository.findAll();
        if (materials.length === 0) return [];

        const allRelations = await this.materialIngredientRepository.findAll();
        const relationsByParent = new Map<string, MaterialIngredient[]>();
        for (const rel of allRelations) {
            const group = relationsByParent.get(rel.materialId) ?? [];
            group.push(rel);
            relationsByParent.set(rel.materialId, group);
        }

        const ingredientIds = [...new Set(allRelations.map(r => r.ingredientId))];
        // 🚀 استفاده از findByIds (بهتر از findAll)
        const ingredients = await this.ingredientRepository.findByIds(ingredientIds);
        const ingredientMap = new Map(ingredients.map(i => [i.id, i]));

        return materials
            .filter((material): material is Material & { id: string } => !!material.id)
            .map(material => {
                const rels = relationsByParent.get(material.id) ?? [];
                const mappedIngredients = rels
                    .map(rel => {
                        const ing = ingredientMap.get(rel.ingredientId);
                        if (!ing || !ing.id) return null; // ing.id حتماً باید موجود باشد
                        return {
                            id: ing.id,
                            name: ing.name,
                            quantity: rel.quantity,
                            category: ing.categoryId ?? 'بدون دسته',
                            unit: rel.unit ?? ing.unit,
                            costPrice: ing.costPrice,
                            currentStock: ing.currentStock,
                        };
                    })
                    .filter((item): item is NonNullable<typeof item> => item !== null);
                return { material, ingredients: mappedIngredients };
            });
    }
}
