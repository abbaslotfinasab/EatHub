// core/domain/repositories/MaterialIngredientRepository.ts
import type {Material} from '../../entities/inventory/Material';
import type {MaterialIngredient} from '../../entities/inventory/MaterialIngredient';
import type {MaterialFilters} from "../../objects/filters/MaterialFilters.ts";



export interface MaterialIngredientRepository {
    create(materialIngredient: MaterialIngredient): Promise<MaterialIngredient>;
    findById(id: string): Promise<Material | null>;
    findByMaterialId(materialId: string): Promise<MaterialIngredient[]>; // 👈 جدید
    findAll(filters?: MaterialFilters): Promise<MaterialIngredient[]>;
    updateWithIngredients(
        id: string,
        data: {
            materialData?: Partial<Omit<Material, 'id'>>;
            ingredients?: Array<{ ingredientId: string; quantity: number; unit?: string }>;
        }
    ): Promise<void>;
    delete(id: string): Promise<void>;
}