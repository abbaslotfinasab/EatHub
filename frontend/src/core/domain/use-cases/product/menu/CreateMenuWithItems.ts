// core/application/use-cases/menu/CreateMenuWithItems.ts
import type {MenuRepository} from '../../../repositories/product/MenuRepository';
import type {MenuFormInput} from "../../../objects/forms/MenuFormInput.ts";



export class CreateMenuWithItems {
    constructor(private menuRepository: MenuRepository) {}

    async execute(input: MenuFormInput) {


        // ارسال به ریپازیتوری (بک‌اند در یک تراکنش منو و آیتم‌ها را ذخیره می‌کند)
        return await this.menuRepository.createWithItems(input); // فرض می‌کنیم result شامل منوی ایجاد شده و آیتم‌ها با idهای تولیدی باشد
    }
}