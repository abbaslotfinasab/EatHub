// core/domain/repositories/MaterialIngredientRepository.ts
import type {Material, UnitType} from '../../entities/inventory/Material';
import type {MaterialIngredient} from '../../entities/inventory/MaterialIngredient';

export interface MaterialFilters {
    search?: string;         // جستجو در name, description
    unit?: UnitType;
    lowStock?: boolean;      // currentStock <= reorderLevel
    isActive?: boolean;      // اگر فیلد isActive دارید (در مدل شما نیست، می‌توانید اضافه کنید)
}

export interface MaterialIngredientRepository {
    create(materialIngredient: MaterialIngredient): Promise<MaterialIngredient>;
    findById(id: string): Promise<Material | null>;
    findByMaterialId(materialId: string): Promise<MaterialIngredient[]>; // 👈 جدید
    findAll(filters?: MaterialFilters): Promise<MaterialIngredient[]>;
    update(id: string, data: Partial<MaterialIngredient>): Promise<MaterialIngredient>;
    delete(id: string): Promise<void>;
}