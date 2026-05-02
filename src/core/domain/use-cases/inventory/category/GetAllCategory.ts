// core/application/use-cases/category/GetAllCategories.ts
import type { CategoryRepository } from '../../../repositories/inventory/CategoryRepository';
import type { Category } from '../../../entities/inventory/Category';
import type { CategoryFilters } from '../../../repositories/inventory/CategoryRepository';

export class GetAllCategories {
    constructor(private readonly categoryRepository: CategoryRepository) {}

    async execute(filters?: CategoryFilters): Promise<Category[]> {
        // (اختیاری) اعتبارسنجی ساده
        if (filters?.search !== undefined && typeof filters.search !== 'string') {
            throw new Error('فیلتر جستجو باید رشته باشد');
        }

        // ارسال درخواست به ریپازیتوری (بک‌اند عملیات فیلتر را انجام می‌دهد)
        return this.categoryRepository.findAll(filters);
    }
}