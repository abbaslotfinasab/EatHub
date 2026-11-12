import { PurchaseRequisitionRepositoryImpl } from '../repositories/PurchaseRequisitionRepositoryImpl.ts';
import {
    ApprovePurchaseRequisition,
    CreatePurchaseRequisition,
    GetPurchaseRequisition,
    GetPurchaseRequisitionDecisions,
    GetPurchaseRequisitionOrderSummary,
    ListPurchaseRequisitions,
    RejectPurchaseRequisition,
    SubmitPurchaseRequisition,
} from '../../domain/use-cases/inventory/purchase/PurchaseRequisitionUseCases.ts';

const repository = new PurchaseRequisitionRepositoryImpl();

export const listPurchaseRequisitions = new ListPurchaseRequisitions(repository);
export const getPurchaseRequisition = new GetPurchaseRequisition(repository);
export const getPurchaseRequisitionOrderSummary = new GetPurchaseRequisitionOrderSummary(repository);
export const getPurchaseRequisitionDecisions = new GetPurchaseRequisitionDecisions(repository);
export const createPurchaseRequisition = new CreatePurchaseRequisition(repository);
export const submitPurchaseRequisition = new SubmitPurchaseRequisition(repository);
export const approvePurchaseRequisition = new ApprovePurchaseRequisition(repository);
export const rejectPurchaseRequisition = new RejectPurchaseRequisition(repository);
