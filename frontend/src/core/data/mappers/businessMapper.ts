// core/data/mappers/businessMapper.ts


import type { Business } from "../../domain/entities/account/Business";
import type { PublicRestaurantDto }
from "../dtos/PublicRestaurantDto";

export const businessMapper = {
    toDomain(
        dto: PublicRestaurantDto
    ): Business {

        return {
            id: dto.id,

            name: dto.name,

            phone: dto.phone_number,

            address: dto.address,

            logo: null,

            logoUrl: dto.logo,
        };
    },
};