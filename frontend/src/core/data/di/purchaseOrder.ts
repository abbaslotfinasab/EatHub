// core/data/di/material.ts
import {CreatePurchaseOrderWithItems} from "../../domain/use-cases/inventory/facture/CreatePurchaseOrderWithItems.ts";
import {PurchaseOrderRepositoryImpl} from "../repositories/PurchaseOrderRepositoryImpl.ts";

const purchaseOrderRepository = new PurchaseOrderRepositoryImpl();

export const createPurchaseOrderUseCase = new CreatePurchaseOrderWithItems(purchaseOrderRepository);
// export const getAllMaterialsUseCase = new GetAllMaterials(materialRepository);
// ... سایر exportها