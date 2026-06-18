// core/domain/repositories/MaterialRepository.ts
import type {Material} from '../../entities/inventory/Material';
import type {MaterialIngredient} from "../../entities/inventory/MaterialIngredient.ts";
import type {MaterialResult} from "../../entities/inventory/MaterialResult.ts";
import type {MaterialFilters} from "./MaterialIngredientRepository.ts";



export interface MaterialRepository {
    creat(
        materialData: Omit<Material, 'id' | 'createdAt' | 'updatedAt'>,
        ingredientsData: Omit<MaterialIngredient, 'id' | 'createdAt' | 'updatedAt' | 'materialId'>[]
    ): Promise<MaterialResult>;
    findById(id: string): Promise<MaterialResult | null>;
    findAll(filters?: MaterialFilters): Promise<MaterialResult[]>;
    update(
        materialId: string,
        materialData: Partial<Omit<Material, 'id' | 'createdAt' | 'updatedAt'>>,
        ingredients?: Omit<MaterialIngredient, 'id' | 'createdAt' | 'updatedAt' | 'materialId'>[]
    ): Promise<MaterialResult>;
    delete(id: string): Promise<void>;
}

