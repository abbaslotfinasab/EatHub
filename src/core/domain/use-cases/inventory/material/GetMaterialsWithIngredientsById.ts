import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';
import type { MaterialIngredientRepository } from '../../../repositories/inventory/MaterialIngredientRepository';
import type { IngredientRepository } from '../../../repositories/inventory/IngredientRepository';
import type {Material} from "../../../entities/inventory/Material.ts";

export interface MaterialWithIngredientsById {
    material: Material;
    ingredients: {
        id: string;
        name: string;
        quantity: number;
        category: string | null;
        unit: string;
        costPrice?: number;
        currentStock: number;
    }[];
}

export class GetMaterialWithIngredientsById {
    constructor(
        private readonly materialRepository: MaterialRepository,
        private readonly materialIngredientRepository: MaterialIngredientRepository,
        private readonly ingredientRepository: IngredientRepository,
    ) {}

    async execute(materialId: string): Promise<MaterialWithIngredientsById | null> {
        // 1. گرفتن ماده اصلی
        const material = await this.materialRepository.findById(materialId);
        if (!material || !material.id) return null;

        // 2. گرفتن روابط این ماده (مواد مصرفی)
        const relations = await this.materialIngredientRepository.findByMaterialId(material.id);
        if (relations.length === 0) {
            return { material, ingredients: [] };
        }

        // 3. جمع‌آوری شناسه مواد مصرفی
        const ingredientIds = [...new Set(relations.map(r => r.ingredientId))];

        // 4. گرفتن جزئیات مواد مصرفی (با findByIds)
        const ingredients = await this.ingredientRepository.findByIds(ingredientIds);
        const ingredientMap = new Map(ingredients.map(i => [i.id, i]));

        // 5. ساخت خروجی تخت
        const mappedIngredients = relations
            .map(rel => {
                const ing = ingredientMap.get(rel.ingredientId);
                if (!ing || !ing.id) return null;
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
    }
}