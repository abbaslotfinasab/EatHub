// core/data/di/material.ts
import { MaterialRepositoryImpl } from '../repositories/MaterialRepositoryImpl';
import {
    CreateMaterialWithIngredients
} from "../../domain/use-cases/inventory/material/CreateMaterialWithIngredients.ts";
import {
    GetAllMaterialsWithIngredients
} from "../../domain/use-cases/inventory/material/GetAllMaterialsWithIngredients.ts";
import {DeleteMaterial} from "../../domain/use-cases/inventory/material/DeleteMaterial.ts";
// سایر UseCaseها...

const materialRepository = new MaterialRepositoryImpl();

export const createMaterialUseCase = new CreateMaterialWithIngredients(materialRepository);
export const getAllMaterialsUseCase = new GetAllMaterialsWithIngredients(materialRepository);
export const deleteMaterialUseCase = new DeleteMaterial(materialRepository)