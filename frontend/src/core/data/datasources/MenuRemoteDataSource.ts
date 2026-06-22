import {apiClient} from "../http/http-client.ts";
import type {MenuDTO} from "../dtos/MenuDto.ts";
import type { CreateMenuDTO } from "../dtos/CreateMenuDTO.ts";
import type {UploadImageResponse} from "../dtos/UploadImageResponse.ts";
import type {PublicRestaurantMenuDto} from "../dtos/PublicRestaurantMenuDto.ts";

export class MenuRemoteDataSource {

   async createMenu(payload: CreateMenuDTO) {
    const { data } = await apiClient.post(
        "/products/menus/create/",
        payload
    );

    return data;
}

   async getMenus(): Promise<MenuDTO[]> {
    const { data } = await apiClient.get<MenuDTO[]>("/products/menus/");
    return data;
}

async getPublicMenus(
    slug: string
): Promise<PublicRestaurantMenuDto> {
    const { data } =
        await apiClient.get(
            `/products/${slug}/menu/`
        );

    return data;
}

  async uploadImage(
        file: File
    ): Promise<UploadImageResponse> {

        const formData = new FormData();

        formData.append("file", file);

        const {data} = await apiClient.post(
            "/products/upload/image/",
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            }
        );

        return data;

    }
}