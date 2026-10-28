// core/data/di/ingredient.ts
import { IngredientRepositoryImpl } from '../repositories/IngredientRepositoryImpl';
import {CreateIngredient} from "../../domain/use-cases/inventory/ingredient/CreateIngredient.ts";
import {GetAllIngredients} from "../../domain/use-cases/inventory/ingredient/GetAllIngredients.ts";
import {DeleteIngredient} from "../../domain/use-cases/inventory/ingredient/DeleteIngredient.ts";
import {GetIngredientById} from "../../domain/use-cases/inventory/ingredient/GetIngredientById.ts";
import {UpdateIngredient} from "../../domain/use-cases/inventory/ingredient/UpdateIngredient.ts";

const ingredientRepository = new IngredientRepositoryImpl();

export const createIngredientUseCase = new CreateIngredient(ingredientRepository);
export const getAllIngredientsUseCase = new GetAllIngredients(ingredientRepository);
export const deleteIngredientUseCase = new DeleteIngredient(ingredientRepository);
export const getIngredientByIdUseCase = new GetIngredientById(ingredientRepository);
export const updateIngredientUseCase = new UpdateIngredient(ingredientRepository);

