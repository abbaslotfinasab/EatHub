import { apiClient } from "../http/http-client.ts";
import type { ProductDTO, ProductInputDTO, ProductPageDTO } from "../dtos/catalog/ProductDTO.ts";

export class ProductCatalogRemoteDataSource {
    async getProducts(params: { page: number; page_size: number; search?: string }): Promise<ProductPageDTO> {
        const { data } = await apiClient.get<ProductPageDTO>("/catalog/products/", { params });
        return data;
    }

    async createProduct(input: ProductInputDTO): Promise<ProductDTO> {
        const { data } = await apiClient.post<ProductDTO>("/catalog/products/", input);
        return data;
    }

    async updateProduct(id: number, input: ProductInputDTO): Promise<ProductDTO> {
        const { data } = await apiClient.patch<ProductDTO>(`/catalog/products/${id}/`, input);
        return data;
    }
}
