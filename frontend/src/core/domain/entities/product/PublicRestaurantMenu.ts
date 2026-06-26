// domain/entities/public-menu/PublicRestaurantMenu.ts


import type {Business} from "../account/Business.ts";
import type {MenuResult} from "./menu/MenuResult.ts";

export interface PublicRestaurantMenu {
    restaurant: Business;

    menus: MenuResult[];
}