// src/core/data/dtos/PublicRestaurantMenuDto.ts

import type { PublicRestaurantDto } from "./PublicRestaurantDto";
import type {MenuDTO} from "./MenuDto.ts";



export interface PublicRestaurantMenuDto {
    restaurant: PublicRestaurantDto;

    menus: MenuDTO[];
}