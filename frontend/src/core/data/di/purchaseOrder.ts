// core/data/di/material.ts
import {CreatePurchaseOrder} from "../../domain/use-cases/inventory/facture/CreatePurchaseOrder.ts";
import {PurchaseOrderRepositoryImpl} from "../repositories/PurchaseOrderRepositoryImpl.ts";

const purchaseOrderRepository = new PurchaseOrderRepositoryImpl();

export const createPurchaseOrderUseCase = new CreatePurchaseOrder(purchaseOrderRepository);
// export const getAllMaterialsUseCase = new GetAllMaterials(materialRepository);
// ... سایر exportها