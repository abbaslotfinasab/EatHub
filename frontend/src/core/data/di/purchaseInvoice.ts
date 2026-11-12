import { PurchaseInvoiceRepositoryImpl } from '../repositories/PurchaseInvoiceRepositoryImpl.ts';
import {
    ApprovePurchaseInvoice,
    CancelPurchaseInvoice,
    CreatePurchaseInvoice,
    GetPurchaseInvoice,
    ListPurchaseInvoices,
    ListPurchaseInvoiceEvents,
    MatchPurchaseInvoice,
    PostPurchaseInvoice,
    UpdatePurchaseInvoice,
} from '../../domain/use-cases/inventory/purchase/PurchaseInvoiceUseCases.ts';

const repository = new PurchaseInvoiceRepositoryImpl();

export const listPurchaseInvoices = new ListPurchaseInvoices(repository);
export const getPurchaseInvoice = new GetPurchaseInvoice(repository);
export const createPurchaseInvoice = new CreatePurchaseInvoice(repository);
export const updatePurchaseInvoice = new UpdatePurchaseInvoice(repository);
export const approvePurchaseInvoice = new ApprovePurchaseInvoice(repository);
export const matchPurchaseInvoice = new MatchPurchaseInvoice(repository);
export const postPurchaseInvoice = new PostPurchaseInvoice(repository);
export const cancelPurchaseInvoice = new CancelPurchaseInvoice(repository);
export const listPurchaseInvoiceEvents = new ListPurchaseInvoiceEvents(repository);
