// core/application/use-cases/menu/GetMenuById.ts
import type { MenuRepository } from '../../../repositories/product/MenuRepository';

export class GetMenuById {
    constructor(private menuRepository: MenuRepository) {}
    async execute(id: number) {
        if (!id) throw new Error('شناسه منو معتبر نیست');
        return this.menuRepository.findMenuItemById(id);
    }
}