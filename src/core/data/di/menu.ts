// core/data/di/menu.ts
import { MenuRepositoryImpl } from '../repositories/MenuRepositoryImpl';
import {CreateMenuWithItems} from "../../domain/use-cases/product/menu/CreateMenuWithItems.ts";

const menuRepository = new MenuRepositoryImpl();

export const createMenuWithItemsUseCase = new CreateMenuWithItems(menuRepository);