// core/application/use-cases/material/GetMaterialWithIngredientsById.ts
import type { MaterialRepository } from '../../../repositories/inventory/MaterialRepository';
import type {MaterialFilters} from "../../../objects/filters/MaterialFilters.ts";
import type {MaterialResult} from "../../../entities/inventory/MaterialResult.ts";

export class GetAllMaterialsWithIngredients {
    constructor(private materialRepository:MaterialRepository) {}
    async execute(filters?: MaterialFilters): Promise<MaterialResult[]> {
        return this.materialRepository.findAll(filters);
    }
}