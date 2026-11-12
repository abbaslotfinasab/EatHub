import { PurchaseSupplierRepositoryImpl } from '../repositories/PurchaseSupplierRepositoryImpl.ts';
import {
    CreatePurchaseSupplier,
    ListPurchaseSuppliers,
    UpdatePurchaseSupplier,
} from '../../domain/use-cases/inventory/purchase/PurchaseSupplierUseCases.ts';

const repository = new PurchaseSupplierRepositoryImpl();

export const listPurchaseSuppliersManagement = new ListPurchaseSuppliers(repository);
export const createPurchaseSupplier = new CreatePurchaseSupplier(repository);
export const updatePurchaseSupplier = new UpdatePurchaseSupplier(repository);
