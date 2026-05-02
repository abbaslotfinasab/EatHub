// core/application/use-cases/material/DeleteMaterial.ts
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';

export class DeleteMaterial {
    constructor(private readonly materialRepository: MaterialRepository) {}

    async execute(materialId: string): Promise<void> {
        if (!materialId) throw new Error('Material ID is required');
        // فراخوانی endpoint حذف در بک‌اند (که خودکار وابسته‌ها را نیز حذف می‌کند)
        await this.materialRepository.delete(materialId);
    }
}