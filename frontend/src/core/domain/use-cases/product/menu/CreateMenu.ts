// core/application/use-cases/menu/CreateMenu.ts
import type {MenuRepository} from '../../../repositories/product/MenuRepository';
import type {MenuWithItems} from "../../../entities/product/menu/MenuWithItems.ts";



export class CreateMenu {
    constructor(private menuRepository: MenuRepository) {}

    async execute(input: MenuWithItems) {


        // ارسال به ریپازیتوری (بک‌اند در یک تراکنش منو و آیتم‌ها را ذخیره می‌کند)
        return await this.menuRepository.create(input); // فرض می‌کنیم result شامل منوی ایجاد شده و آیتم‌ها با idهای تولیدی باشد
    }
}