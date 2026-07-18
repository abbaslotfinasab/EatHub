// core/data/mappers/publicRestaurantMenuMapper.ts

import type { PublicRestaurantMenuDto }
from "../dtos/business/PublicRestaurantMenuDto.ts";
import { businessMapper } from "./businessMapper";
import {menuMapper} from "./menuMapper.ts";
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