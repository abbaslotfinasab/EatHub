// core/application/use-cases/menu/GetAllMenus.ts
import type { MenuRepository } from '../../../repositories/product/MenuRepository';
import type {MenuWithItems} from "../../../entities/product/menu/MenuWithItems.ts";

export interface MenuFilters {
    isActive?: boolean;
    search?: string;
}

export class GetAllMenus {
    constructor(private menuRepository: MenuRepository) {}
    async execute(filters?: MenuFilters): Promise<MenuWithItems[]> {
        return this.menuRepository.findAll(filters);
    }
}