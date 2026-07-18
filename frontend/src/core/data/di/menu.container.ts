// data/di/menu.container.ts



import { CreateMenu } from "../../domain/use-cases/product/menu/CreateMenu.ts";
import { GetAllMenus } from "../../domain/use-cases/product/menu/GetAllMenus";
import {MenuRepositoryImpl} from "../repositories/MenuRepositoryImpl.ts";
import {MenuRemoteDataSource} from "../datasources/MenuRemoteDataSource.ts";
import {GetPublicMenus} from "../../domain/use-cases/product/menu/GetPublicMenus.ts";
import {GetMenuById} from "../../domain/use-cases/product/menu/GetMenuById.ts";
import {UpdateMenu} from "../../domain/use-cases/product/menu/UpdateMenu.ts";
import {DeleteMenu} from "../../domain/use-cases/product/menu/DeleteMenu.ts";

export const createMenuContainer = () => {
    const remote = new MenuRemoteDataSource();
    const repository = new MenuRepositoryImpl(remote);

    return {
        createMenuWithItemsUseCase: new CreateMenu(repository),
        getAllMenusUseCase: new GetAllMenus(repository),
        getMenuByIdUseCase: new GetMenuById(repository),
        getPublicMenusUseCase: new GetPublicMenus(repository),
        updateMenuWithItemsUseCase: new UpdateMenu(repository),
        deleteMenuUseCase: new DeleteMenu(repository),



    };
};