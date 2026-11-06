import { PurchaseReceivingRepositoryImpl } from '../repositories/PurchaseReceivingRepositoryImpl.ts';
import {
    CancelPurchaseOrder,
    CreateOrderGoodsReceipt,
    CreatePurchaseOrder,
    GetReceivingOrder,
    ListOrderGoodsReceipts,
    ListPurchaseSuppliers,
    ListReceivingOrders,
    SendPurchaseOrder,
    UpdatePurchaseOrder,
} from '../../domain/use-cases/inventory/purchase/PurchaseReceivingUseCases.ts';

const repository = new PurchaseReceivingRepositoryImpl();

export const listReceivingOrders = new ListReceivingOrders(repository);
export const getReceivingOrder = new GetReceivingOrder(repository);
export const createPurchaseOrder = new CreatePurchaseOrder(repository);
export const updatePurchaseOrder = new UpdatePurchaseOrder(repository);
export const sendPurchaseOrder = new SendPurchaseOrder(repository);
export const cancelPurchaseOrder = new CancelPurchaseOrder(repository);
export const listOrderGoodsReceipts = new ListOrderGoodsReceipts(repository);
export const createOrderGoodsReceipt = new CreateOrderGoodsReceipt(repository);
export const listPurchaseSuppliers = new ListPurchaseSuppliers(repository);
