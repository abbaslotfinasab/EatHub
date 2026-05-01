// domain/use-cases/ingredient/DeleteIngredient.ts
import type { IngredientRepository } from '../../../repositories/inventory/IngredientRepository.ts';

export class DeleteIngredient {
    constructor(private ingredientRepository: IngredientRepository) {}

    async execute(id: string): Promise<void> {
        if (!id || id.trim() === '') {
            throw new Error('شناسه ماده اولیه معتبر نیست');
        }

        // (اختیاری) بررسی وجود ماده قبل از حذف
        const existing = await this.ingredientRepository.findById(id);
        if (!existing) {
            throw new Error('ماده اولیه یافت نشد');
        }

        // حذف از طریق ریپازیتوری (بک‌اند مسئول بررسی وابستگی‌هاست)
        await this.ingredientRepository.delete(id);
    }
}