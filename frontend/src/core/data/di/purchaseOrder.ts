// core/data/di/material.ts
import {CreatePurchaseOrder} from "../../domain/use-cases/inventory/facture/CreatePurchaseOrder.ts";
import {PurchaseOrderRemoteDataSource} from "../datasources/PurchaseOrderRemoteDataSource.ts";
import {PurchaseOrderRepositoryImpl} from "../repositories/PurchaseOrderRepositoryImpl.ts";

 const remote =
        new PurchaseOrderRemoteDataSource();

    const repository =
        new PurchaseOrderRepositoryImpl(
            remote,
        );

export const createPurchaseOrderUseCase = new CreatePurchaseOrder(repository);
// export const getAllMaterialsUseCase = new GetAllMaterials(materialRepository);
// ... سایر exportها