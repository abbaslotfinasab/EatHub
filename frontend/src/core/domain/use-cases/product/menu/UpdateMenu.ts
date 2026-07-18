// core/application/use-cases/menu/UpdateMenu.ts
import type { MenuRepository } from '../../../repositories/product/MenuRepository';
import type { MenuWithItems } from '../../../entities/product/menu/MenuWithItems.ts';


export class UpdateMenu {
    constructor(private menuRepository: MenuRepository) {}

    async execute(input: MenuWithItems){
        if (!input.menu.id) throw new Error('شناسه منو معتبر نیست');


        // ارسال به ریپازیتوری (بک‌اند اعتبارسنجی و جایگزینی آیتم‌ها را انجام می‌دهد)
        return await this.menuRepository.update(input);
    }
}