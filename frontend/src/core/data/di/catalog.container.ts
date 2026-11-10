import { ProductCatalogRemoteDataSource } from "../datasources/ProductCatalogRemoteDataSource.ts";
import { ProductCatalogRepositoryImpl } from "../repositories/ProductCatalogRepositoryImpl.ts";

export const createCatalogContainer = () => {
    const remote = new ProductCatalogRemoteDataSource();
    const repository = new ProductCatalogRepositoryImpl(remote);
    return { productRepository: repository };
};
