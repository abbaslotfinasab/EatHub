// data/di/menu.container.ts



import { CreateMenuWithItems } from "../../domain/use-cases/product/menu/CreateMenuWithItems";
import { GetAllMenus } from "../../domain/use-cases/product/menu/GetAllMenus";
import {MenuRepositoryImpl} from "../repositories/MenuRepositoryImpl.ts";
import {MenuRemoteDataSource} from "../datasources/MenuRemoteDataSource.ts";
import {GetPublicMenus} from "../../domain/use-cases/product/menu/GetPublicMenus.ts";

export const createMenuContainer = () => {
    const remote = new MenuRemoteDataSource();
    const repository = new MenuRepositoryImpl(remote);

    return {
        createMenuWithItemsUseCase: new CreateMenuWithItems(repository),
        getAllMenusUseCase: new GetAllMenus(repository),
        getPublicMenusUseCase: new GetPublicMenus(repository),

    };
};