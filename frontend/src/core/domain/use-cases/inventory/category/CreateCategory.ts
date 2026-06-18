// core/application/use-cases/category/CreateCategory.ts
import type { CategoryRepository } from '../../../repositories/inventory/CategoryRepository';
import { z } from 'zod';
import {Unit} from "../../../entities/inventory/Category";


const CreateCategorySchema = z.object({
    name: z.string().min(2, 'نام دسته‌بندی حداقل ۲ کاراکتر است').trim(),
    unit: z.enum(Unit, { message: 'واحد معتبر نیست' }),
    isActive: z.boolean().optional().default(true),
});

export type CreateCategoryInput = z.infer<typeof CreateCategorySchema>;

export class CreateCategory {
    constructor(private readonly categoryRepository: CategoryRepository) {}

    async execute(input: CreateCategoryInput): Promise<void> {
        // 1. اعتبارسنجی
        const validated = CreateCategorySchema.parse(input);


        // 3. ارسال به ریپازیتوری (بک‌اند بقیه را انجام می‌دهد)
        await this.categoryRepository.create(validated);
    }
}