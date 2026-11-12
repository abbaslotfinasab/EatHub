import { PurchaseRequisitionRepositoryImpl } from '../repositories/PurchaseRequisitionRepositoryImpl.ts';
import {
    GetPurchaseRequisition,
    GetPurchaseRequisitionDecisions,
    GetPurchaseRequisitionOrderSummary,
    ListPurchaseRequisitions,
} from '../../domain/use-cases/inventory/purchase/PurchaseRequisitionUseCases.ts';

const repository = new PurchaseRequisitionRepositoryImpl();

export const listPurchaseRequisitions = new ListPurchaseRequisitions(repository);
export const getPurchaseRequisition = new GetPurchaseRequisition(repository);
export const getPurchaseRequisitionOrderSummary = new GetPurchaseRequisitionOrderSummary(repository);
export const getPurchaseRequisitionDecisions = new GetPurchaseRequisitionDecisions(repository);
