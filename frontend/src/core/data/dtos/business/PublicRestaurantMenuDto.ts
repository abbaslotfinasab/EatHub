// src/core/data/dtos/PublicRestaurantMenuDto.ts

import type { PublicRestaurantDto } from "./PublicRestaurantDto.ts";
import type {MenuDTO} from "../menu/MenuDto.ts";



export interface PublicRestaurantMenuDto {
    restaurant: PublicRestaurantDto;

    menus: MenuDTO[];
}