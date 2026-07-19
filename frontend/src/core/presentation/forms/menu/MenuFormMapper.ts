// core/presentation/forms/menu/MenuFormMapper.ts

import type { MenuFormInput } from "./MenuFormInput";
import type { MenuWithItems } from "../../../domain/entities/product/menu/MenuWithItems";

export class MenuFormMapper {
    static toDomain(input: MenuFormInput): MenuWithItems {
        return {
            menu: {
                name: input.name,

                category: input.category,

                description: input.description,

                sortOrder: input.sortOrder,

                isActive: input.isActive,

            },

            items: input.items.map((item) => ({
                id: item.id?
                    Number(item.id)
                    : null,

                name: item.name,

                description: item.description,

                price: item.price,

                imageUrl: item.imageUrl,

                isAvailable: item.isAvailable,

            })),
        };
    }

    static toFormInput(menu: MenuWithItems): MenuFormInput {
        return {
            name: menu.menu.name,

            category: menu.menu.category,

            description: menu.menu.description,

            sortOrder: menu.menu.sortOrder,

            isActive: menu.menu.isActive,

            items: menu.items.map((item) => ({

                name: item.name,

                description: item.description,

                price: item.price,

                imageUrl: item.imageUrl,

                isAvailable: item.isAvailable,
            })),
        };
    }
}