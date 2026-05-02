// core/application/use-cases/category/DeleteCategory.ts
import type { CategoryRepository } from '../../../repositories/inventory/CategoryRepository';

export class DeleteCategory {
    constructor(private readonly categoryRepository: CategoryRepository) {}

    async execute(id: string): Promise<void> {
        if (!id || id.trim() === '') {
            throw new Error('شناسه دسته‌بندی معتبر نیست');
        }

        // (اختیاری) بررسی وجود دسته‌بندی برای خطای سریع‌تر
        const existing = await this.categoryRepository.findById(id);
        if (!existing) {
            throw new Error('دسته‌بندی یافت نشد');
        }

        // ارسال درخواست حذف به بک‌اند
        await this.categoryRepository.delete(id);
    }
}