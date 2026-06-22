// core/application/use-cases/menu/CreateMenuWithItems.ts
import {z} from 'zod';
import type {MenuRepository} from '../../../repositories/product/MenuRepository';

// شمای هر آیتم منو
export const MenuItemSchema = z.object({
    name: z.string().min(2),
    description: z.string().nullable(),
    price: z.coerce.number().int().positive(),
    imageFile: z.instanceof(File).nullable(),
    isAvailable: z.boolean(),
    recipeId: z.string(),
    // در صورت نیاز فیلدهای دیگر
});

// شمای اصلی شامل منو و آیتم‌ها
export const CreateMenuWithItemsSchema = z.object({
    name: z.string().min(2).trim(),
    category: z.string().min(1),
    description: z.string().nullable(),
    sortOrder: z.coerce.number().int(),
    isActive: z.boolean(),
    items: z.array(MenuItemSchema).min(1, 'حداقل یک آیتم برای منو الزامی است'),
});

export type CreateMenuWithItemsInput = z.input<typeof CreateMenuWithItemsSchema>;

export class CreateMenuWithItems {
    constructor(private menuRepository: MenuRepository) {}

    async execute(input: CreateMenuWithItemsInput) {
        const validated = CreateMenuWithItemsSchema.parse(input);

        const { items, ...menu } = validated;

        // ارسال به ریپازیتوری (بک‌اند در یک تراکنش منو و آیتم‌ها را ذخیره می‌کند)
        return await this.menuRepository.createWithItems(menu, items); // فرض می‌کنیم result شامل منوی ایجاد شده و آیتم‌ها با idهای تولیدی باشد
    }
}