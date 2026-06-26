// core/application/use-cases/menu/GetAllMenus.ts
import type { MenuRepository } from '../../../repositories/product/MenuRepository';
import type {MenuResult} from "../../../entities/product/menu/MenuResult.ts";

export interface MenuFilters {
    isActive?: boolean;
    search?: string;
}

export class GetAllMenus {
    constructor(private menuRepository: MenuRepository) {}
    async execute(filters?: MenuFilters): Promise<MenuResult[]> {
        return this.menuRepository.findAll(filters);
    }
}