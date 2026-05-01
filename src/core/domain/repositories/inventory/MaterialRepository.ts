// core/domain/repositories/MaterialRepository.ts
import type {Material, UnitType} from '../../entities/inventory/Material';

export interface MaterialFilters {
    search?: string;         // جستجو در name, description
    unit?: UnitType;
    lowStock?: boolean;      // currentStock <= reorderLevel
    isActive?: boolean;      // اگر فیلد isActive دارید (در مدل شما نیست، می‌توانید اضافه کنید)
}

export interface MaterialRepository {
    create(material: Material): Promise<Material>;
    findById(id: string): Promise<Material | null>;
    findAll(filters?: MaterialFilters): Promise<Material[]>;
    update(id: string, data: Partial<Material>): Promise<Material>;
    delete(id: string): Promise<void>;
    updateStock(id: string, newStock: number): Promise<void>;
}

