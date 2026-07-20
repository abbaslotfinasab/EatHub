import type { MenuDTO } from "../dtos/menu/MenuDto.ts";
import type { MenuItemDTO } from "../dtos/menu/MenuItemDTO.ts";

import type { Menu } from "../../domain/entities/product/menu/Menu.ts";
import type { MenuItem } from "../../domain/entities/product/menu/MenuItem.ts";
import type { MenuWithItems } from "../../domain/entities/product/menu/MenuWithItems.ts";

import type { UpdateMenuDTO } from "../dtos/menu/UpdateMenuDTO.ts";
import type { UpdateMenuItemDTO } from "../dtos/menu/UpdateMenuItemDTO.ts";
import type {CreateMenuDTO} from "../dtos/menu/CreateMenuDTO.ts";
import type { CreateMenuItemDTO } from "../dtos/menu/CreateMenuItemDTO.ts";

export const menuMapper = {
    // =========================
    // DTO → DOMAIN
    // =========================

    toDomain(dto: MenuDTO): MenuWithItems {
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
            menuId: dto.menuId,
            name: dto.name,
            description: dto.description,
            price: dto.price,
            imageUrl: dto.image_url,
            isAvailable: dto.is_available,
            createdAt: dto.created_at,
            updatedAt: dto.updated_at,
        };
    },

     toCreateDTO(domain: MenuWithItems): CreateMenuDTO {
        return {
            name: domain.menu.name,
            category: domain.menu.category,
            description: domain.menu.description,
            sort_order: domain.menu.sortOrder,
            items: domain.items.map(menuMapper.toCreateMenuItemDTO),
        };
    },

    toCreateMenuItemDTO(domain: MenuItem): CreateMenuItemDTO {
        return {
            name: domain.name,
            description: domain.description,
            price: domain.price,
            image_url: domain.imageUrl,
        };
    },

    // =========================
    // DOMAIN → UPDATE DTO
    // =========================

    toUpdateDTO(domain: MenuWithItems): UpdateMenuDTO {
        return {
            id: domain.menu.id?? -1,
            name: domain.menu.name,
            category: domain.menu.category,
            description: domain.menu.description,
            sort_order: domain.menu.sortOrder,
            items: domain.items.map(menuMapper.toUpdateMenuItemDTO),
        };
    },

    toUpdateMenuItemDTO(domain: MenuItem): UpdateMenuItemDTO {
        return {
            id: domain.id ?? -1,
            name: domain.name,
            description: domain.description,
            price: domain.price,
            image_url: domain.imageUrl,
        };
    },
};