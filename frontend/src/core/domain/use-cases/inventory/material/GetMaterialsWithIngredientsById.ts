// core/application/use-cases/material/GetMaterialWithIngredientsById.ts
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';
import type {MaterialResult} from "../../../entities/inventory/MaterialResult.ts";

export class GetMaterialWithIngredientsById {
    constructor(private materialRepository: MaterialRepository) {}

    async execute(materialId: string): Promise<MaterialResult | null> {
        if (!materialId) throw new Error('شناسه ماده معتبر نیست');
        return this.materialRepository.findById(materialId);
    }
}