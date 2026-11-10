import type { Product, ProductInput, ProductPage } from "../../entities/catalog/Product.ts";

export interface ProductRepository {
    findAll(filters: { page: number; pageSize: number; search?: string }): Promise<ProductPage>;
    create(input: ProductInput): Promise<Product>;
    update(id: number, input: Partial<ProductInput>): Promise<Product>;
}
