import { apiClient } from "../http/http-client";

import type { MenuDTO } from "../dtos/MenuDto";
import type { CreateMenuDTO } from "../dtos/CreateMenuDTO";
import type { UploadImageResponse } from "../dtos/UploadImageResponse";
import type { PublicRestaurantMenuDto } from "../dtos/PublicRestaurantMenuDto";

export class MenuRemoteDataSource {

    async createMenu(payload: CreateMenuDTO): Promise<MenuDTO> {
        const { data } = await apiClient.post<MenuDTO>(
            "/products/menus/create/",
            payload,
        );

        return data;
    }

    async getMenus(): Promise<MenuDTO[]> {
        const { data } = await apiClient.get<MenuDTO[]>(
            "/products/menus/",
        );

        return data;
    }

    async getMenuById(id: string): Promise<MenuDTO> {
        const { data } = await apiClient.get<MenuDTO>(
            `/products/menus/${id}/`,
        );

        return data;
    }

    async updateMenu(
        id: string,
        payload: CreateMenuDTO,
    ): Promise<MenuDTO> {
        const { data } = await apiClient.patch<MenuDTO>(
            `/products/menus/${id}/update/`,
            payload,
        );

        return data;
    }

    async deleteMenu(id: string): Promise<void> {
        await apiClient.delete(
            `/products/menus/${id}/delete/`,
        );
    }

    async getPublicMenus(
        slug: string,
    ): Promise<PublicRestaurantMenuDto> {
        const { data } = await apiClient.get<PublicRestaurantMenuDto>(
            `/products/${slug}/menu/`,
        );

        return data;
    }

    async uploadImage(
        file: File,
    ): Promise<UploadImageResponse> {
        const formData = new FormData();

        formData.append("file", file);

        const { data } = await apiClient.post<UploadImageResponse>(
            "/products/upload/image/",
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            },
        );

        return data;
    }
}