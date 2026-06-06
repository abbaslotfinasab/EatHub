// core/application/use-cases/menu/DeleteMenu.ts
import type { MenuRepository } from '../../../repositories/product/MenuRepository';

export class DeleteMenu {
    constructor(private menuRepository: MenuRepository) {}
    async execute(id: string) {
        if (!id) throw new Error('شناسه منو معتبر نیست');
        await this.menuRepository.delete(id);
    }
}