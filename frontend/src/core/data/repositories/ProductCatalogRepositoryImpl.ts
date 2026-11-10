import type { Product, ProductInput, ProductPage } from "../../domain/entities/catalog/Product.ts";
import type { ProductRepository } from "../../domain/repositories/catalog/ProductRepository.ts";
import { ProductCatalogRemoteDataSource } from "../datasources/ProductCatalogRemoteDataSource.ts";
import { productCatalogMapper } from "../mappers/productCatalogMapper.ts";

export class ProductCatalogRepositoryImpl implements ProductRepository {
    constructor(private readonly remote: ProductCatalogRemoteDataSource) {}

    async findAll(filters: { page: number; pageSize: number; search?: string }): Promise<ProductPage> {
        const dto = await this.remote.getProducts({
            page: filters.page,
            page_size: filters.pageSize,
            ...(filters.search ? { search: filters.search } : {}),
        });
        return productCatalogMapper.toPage(dto);
    }

    async create(input: ProductInput): Promise<Product> {
        return productCatalogMapper.toDomain(
            await this.remote.createProduct(productCatalogMapper.toInputDTO(input))
        );
    }

    async update(id: number, input: Partial<ProductInput>): Promise<Product> {
        return productCatalogMapper.toDomain(
            await this.remote.updateProduct(id, productCatalogMapper.toInputDTO(input))
        );
    }
}
