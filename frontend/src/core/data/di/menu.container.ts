// data/di/menu.container.ts



import { CreateMenuWithItems } from "../../domain/use-cases/product/menu/CreateMenuWithItems";
import { GetAllMenus } from "../../domain/use-cases/product/menu/GetAllMenus";
import {MenuRepositoryImpl} from "../repositories/MenuRepositoryImpl.ts";
import {MenuRemoteDataSource} from "../datasources/MenuRemoteDataSource.ts";
import {GetPublicMenus} from "../../domain/use-cases/product/menu/GetPublicMenus.ts";
import {GetMenuById} from "../../domain/use-cases/product/menu/GetMenuById.ts";
import {UpdateMenuWithItems} from "../../domain/use-cases/product/menu/UpdateMenuWithItems.ts";
import {DeleteMenu} from "../../domain/use-cases/product/menu/DeleteMenu.ts";

export const createMenuContainer = () => {
    const remote = new MenuRemoteDataSource();
    const repository = new MenuRepositoryImpl(remote);

    return {
        createMenuWithItemsUseCase: new CreateMenuWithItems(repository),
        getAllMenusUseCase: new GetAllMenus(repository),
        getMenuByIdUseCase: new GetMenuById(repository),
        getPublicMenusUseCase: new GetPublicMenus(repository),
        updateMenuWithItemsUseCase: new UpdateMenuWithItems(repository),
        deleteMenuUseCase: new DeleteMenu(repository),



    };
};