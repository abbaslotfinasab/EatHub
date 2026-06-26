// core/application/use-cases/menu/UpdateMenuWithItems.ts
import type { MenuRepository } from '../../../repositories/product/MenuRepository';
import type { MenuResult } from '../../../entities/product/menu/MenuResult.ts';
import type {MenuFormInput} from "../../../objects/forms/MenuFormInput.ts";


export class UpdateMenuWithItems {
    constructor(private menuRepository: MenuRepository) {}

    async execute(menuId: string, input: MenuFormInput): Promise<MenuResult> {
        if (!menuId) throw new Error('شناسه منو معتبر نیست');


        // ارسال به ریپازیتوری (بک‌اند اعتبارسنجی و جایگزینی آیتم‌ها را انجام می‌دهد)
        return await this.menuRepository.update(menuId, input);
    }
}