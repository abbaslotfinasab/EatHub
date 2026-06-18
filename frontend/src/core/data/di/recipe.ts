// src/presentation/di.ts

import {RecipeRepositoryImpl} from "../repositories/RecipeRepositoryImpl.ts";
import {CreateRecipeWithComponents} from "../../domain/use-cases/product/recipe/CreateRecipeWithComponents.ts";
import {GetAllRecipeWithComponents} from "../../domain/use-cases/product/recipe/GetAllRecipeWithComponents.ts";
import {DeleteRecipe} from "../../domain/use-cases/product/recipe/DeleteRecipe.ts";

const recipeRepository = new RecipeRepositoryImpl();

export const createRecipeUseCase = new CreateRecipeWithComponents(recipeRepository);
export const getAllRecipesUseCase = new GetAllRecipeWithComponents(recipeRepository);
export const deleteRecipeUseCase = new DeleteRecipe(recipeRepository);
