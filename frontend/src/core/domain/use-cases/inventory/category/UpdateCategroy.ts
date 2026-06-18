// core/application/use-cases/category/UpdateCategory.ts
import { z } from 'zod';
import type { CategoryRepository } from '../../../repositories/inventory/CategoryRepository';
import {Unit} from "../../../entities/inventory/Category.ts";


const UpdateCategorySchema = z.object({
    name: z.string().min(2, 'نام دسته‌بندی حداقل ۲ کاراکتر است').trim().optional(),
    unit: z.enum(Unit, { message: 'واحد معتبر نیست' }).optional(),
    isActive: z.boolean().optional().default(true),
});

export type UpdateCategoryInput = z.infer<typeof UpdateCategorySchema>;

export class UpdateCategory {
    constructor(private readonly categoryRepository: CategoryRepository) {}

    async execute(id: string, input: UpdateCategoryInput): Promise<void> {
        if (!id || id.trim() === '') {
            throw new Error('شناسه دسته‌بندی معتبر نیست');
        }

        // 1. اعتبارسنجی ورودی
        const validated = UpdateCategorySchema.parse(input);

        // 2. (اختیاری) بررسی وجود دسته‌بندی برای خطای سریع‌تر
        const existing = await this.categoryRepository.findById(id);
        if (!existing) {
            throw new Error('دسته‌بندی یافت نشد');
        }
        //
        // // 3. تبدیل undefined به null برای فیلدهای nullable
        // const dataForRepo: Record<string, unknown> = {};
        // if (validated.name !== undefined) dataForRepo.name = validated.name;
        // if (validated.parentId !== undefined) dataForRepo.parentId = validated.parentId ?? null;
        // if (validated.description !== undefined) dataForRepo.description = validated.description ?? null;

        // 4. ارسال درخواست به ریپازیتوری (بک‌اند)
        await this.categoryRepository.update(id, validated);
    }
}