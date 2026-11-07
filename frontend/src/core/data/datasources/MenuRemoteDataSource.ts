import { apiClient } from "../http/http-client";

import type { MenuDTO } from "../dtos/menu/MenuDto.ts";
import type { CreateMenuDTO } from "../dtos/menu/CreateMenuDTO.ts";
import type { UpdateMenuDTO } from "../dtos/menu/UpdateMenuDTO.ts";
import type { UpdateMenuItemDTO } from "../dtos/menu/UpdateMenuItemDTO.ts";
import type { MenuItemDTO } from "../dtos/menu/MenuItemDTO.ts";
import type { PublicRestaurantMenuDto } from "../dtos/business/PublicRestaurantMenuDto.ts";

export class MenuRemoteDataSource {
    async createMenu(payload: CreateMenuDTO): Promise<MenuDTO> {
        const { data } = await apiClient.post<MenuDTO>("/products/menus/create/", payload);
        return data;
    }

    async getMenus(): Promise<MenuDTO[]> {
        const { data } = await apiClient.get<MenuDTO[]>("/products/menus/");
        return data;
    }

    async getMenuById(id: number): Promise<MenuDTO> {
        const { data } = await apiClient.get<MenuDTO>(`/products/menus/${id}/`);
        return data;
    }

    async updateMenu(id: number, payload: UpdateMenuDTO): Promise<MenuDTO> {
        const { data } = await apiClient.patch<MenuDTO>(`/products/menus/${id}/update/`, payload);
        return data;
    }

    async deleteMenu(id: string): Promise<void> {
        await apiClient.delete(`/products/menus/${id}/delete/`);
    }

    async updateMenuItem(id: number, payload: UpdateMenuItemDTO): Promise<MenuItemDTO> {
        const { data } = await apiClient.patch<MenuItemDTO>(`/products/menu-items/${id}/update/`, payload);
        return data;
    }

    async deleteMenuItem(id: number): Promise<void> {
        await apiClient.delete(`/products/menu-items/${id}/delete/`);
    }

    async getPublicMenus(slug: string): Promise<PublicRestaurantMenuDto> {
        const { data } = await apiClient.get<PublicRestaurantMenuDto>(`/products/${slug}/menu/`);
        return data;
    }
}
