// core/application/use-cases/menu/UpdateMenuWithItems.ts
import { z } from 'zod';
import type { MenuRepository } from '../../../repositories/product/MenuRepository';
import type { MenuResult } from '../../../entities/product/MenuResult';

// شمای هر آیتم منو (برای جایگزینی کامل)
const MenuItemUpdateSchema = z.object({
    id: z.string().optional(), // اگر id داشته باشد، برای به‌روزرسانی، اگر نداشته باشد، ایجاد جدید
    name: z.string().min(2),
    description: z.string().nullable().optional(),
    price: z.number().positive(),
    imageUrl: z.string().url().nullable().optional(),
    isAvailable: z.boolean().default(true),
    recipeId: z.string(),
});

// شمای اصلی ورودی
const UpdateMenuWithItemsSchema = z.object({
    menu: z.object({
        name: z.string().min(2).trim().optional(),
        category: z.string().min(1).optional(),
        description: z.string().nullable().optional(),
        sortOrder: z.number().int().optional(),
        isActive: z.boolean().optional(),
    }),
    items: z.array(MenuItemUpdateSchema).optional(), // اگر ارسال شود، جایگزین کامل آیتم‌های قبلی می‌شود
});

export type UpdateMenuWithItemsInput = z.infer<typeof UpdateMenuWithItemsSchema>;

export class UpdateMenuWithItems {
    constructor(private menuRepository: MenuRepository) {}

    async execute(menuId: string, input: UpdateMenuWithItemsInput): Promise<MenuResult> {
        if (!menuId) throw new Error('شناسه منو معتبر نیست');

        const validated = UpdateMenuWithItemsSchema.parse(input);

        // ارسال به ریپازیتوری (بک‌اند اعتبارسنجی و جایگزینی آیتم‌ها را انجام می‌دهد)
        return await this.menuRepository.update(menuId, validated.menu, validated.items);
    }
}