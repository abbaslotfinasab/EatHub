// core/application/use-cases/category/GetCategoryById.ts
import type { CategoryRepository } from '../../../repositories/inventory/CategoryRepository';
import type { Category } from '../../../entities/inventory/Category';

export class GetCategoryById {
    constructor(private readonly categoryRepository: CategoryRepository) {}

    async execute(id: string): Promise<Category | null> {
        if (!id || id.trim() === '') {
            throw new Error('شناسه دسته‌بندی معتبر نیست');
        }

        return this.categoryRepository.findById(id);
    }
}