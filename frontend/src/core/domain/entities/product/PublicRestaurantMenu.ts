// domain/entities/public-menu/PublicRestaurantMenu.ts


import type {Business} from "../account/Business.ts";
import type {MenuWithItems} from "./menu/MenuWithItems.ts";

export interface PublicRestaurantMenu {
    restaurant: Business;

    menus: MenuWithItems[];
}