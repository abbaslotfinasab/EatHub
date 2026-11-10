import type { Product, ProductInput, ProductPage } from "../../domain/entities/catalog/Product.ts";
import type { ProductDTO, ProductInputDTO, ProductPageDTO } from "../dtos/catalog/ProductDTO.ts";

export const productCatalogMapper = {
    toDomain(dto: ProductDTO): Product {
        return {
            id: dto.id,
            name: dto.name,
            sku: dto.sku,
            category: dto.category,
            description: dto.description,
            imageUrl: dto.image_url,
            status: dto.status,
            createdAt: dto.created_at,
            updatedAt: dto.updated_at,
        };
    },

    toInputDTO(input: ProductInput | Partial<ProductInput>): ProductInputDTO {
        return {
            ...(input.name !== undefined ? { name: input.name } : {}),
            ...(input.sku !== undefined ? { sku: input.sku } : {}),
            ...(input.category !== undefined ? { category: input.category } : {}),
            ...(input.description !== undefined ? { description: input.description } : {}),
            ...(input.imageUrl !== undefined ? { image_url: input.imageUrl } : {}),
            ...(input.status !== undefined ? { status: input.status } : {}),
        };
    },

    toPage(dto: ProductPageDTO): ProductPage {
        return {
            count: dto.count,
            page: dto.page,
            pageSize: dto.page_size,
            results: dto.results.map(this.toDomain),
        };
    },
};
