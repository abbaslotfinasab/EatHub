import { createMenuContainer } from "./menu.container";

const container = createMenuContainer();

export const createMenuWithItemsUseCase =
    container.createMenuWithItemsUseCase;

export const getAllMenusUseCase =
    container.getAllMenusUseCase;