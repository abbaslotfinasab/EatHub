// src/core/data/dtos/PublicRestaurantDto.ts

export interface PublicRestaurantDto {
    id: string;

    name: string;

    description: string;

    slug: string;

    logo: string | null;

    phone_number: string;

    address: string;

    is_active: boolean;

    created_at: string;

    updated_at: string;
}