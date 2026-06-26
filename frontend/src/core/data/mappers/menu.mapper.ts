import type { MenuDTO } from "../dtos/MenuDto";
import type {Menu} from "../../domain/entities/product/menu/Menu.ts";
import type { MenuItemDTO } from "../dtos/MenuItemDTO.ts";
import type {MenuItem} from "../../domain/entities/product/menu/MenuItem.ts";
import type {MenuResult} from "../../domain/entities/product/menu/MenuResult.ts";
import type {MenuFormInput} from "../../domain/objects/forms/MenuFormInput.ts";

export const menuMapper = {
    toDomain(dto: MenuDTO): MenuResult {
        return {
            menu: menuMapper.toMenu(dto),
            items: (dto.items ?? []).map(menuMapper.toMenuItem),
        };
    },

    toMenu(dto: MenuDTO): Menu {
        return {
            id: dto.id,
            name: dto.name,
            category: dto.category,
            description: dto.description,
            sortOrder: dto.sort_order,
            isActive: dto.is_active,
            createdAt: dto.created_at,
            updatedAt: dto.updated_at,
        };
    },

    toMenuItem(dto: MenuItemDTO): MenuItem {
        return {
            id: dto.id,
            name: dto.name,
            description: dto.description,
            price: dto.price,
            imageUrl: dto.image_url, // مهم
            imageFile: null,
            menuId: "",
            isAvailable: dto.is_available,
            createdAt: dto.created_at,
            updatedAt: dto.updated_at,
        };
    },


    toFormInput(menu: MenuResult): MenuFormInput {
        return {
            name: menu.menu.name,
            category: menu.menu.category,
            description: menu.menu.description,
            sortOrder: menu.menu.sortOrder,
            isActive: menu.menu.isActive,

            items: menu.items.map(item => ({

                id: item.id ? String(item.id) : undefined, // 👈 مهم

                name: item.name,

                description: item.description,

                price: item.price,

                imageFile: null,

                imageUrl: item.imageUrl,

                isAvailable: item.isAvailable,

            })),
        };
    },


};