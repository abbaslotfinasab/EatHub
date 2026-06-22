// core/data/mappers/publicRestaurantMenuMapper.ts

import type { PublicRestaurantMenuDto }
from "../dtos/PublicRestaurantMenuDto";
import { businessMapper } from "./businessMapper";
import {menuMapper} from "./menu.mapper.ts";
import type {PublicRestaurantMenu} from "../../domain/entities/product/PublicRestaurantMenu.ts";


export const publicRestaurantMenuMapper = {

    toDomain(
        dto: PublicRestaurantMenuDto
    ): PublicRestaurantMenu {

        return {

            restaurant:
                businessMapper.toDomain(
                    dto.restaurant
                ),

            menus:
                dto.menus.map(
                    menuMapper.toDomain
                ),
        };
    },
};