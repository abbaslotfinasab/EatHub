import { PurchaseReceivingRepositoryImpl } from '../repositories/PurchaseReceivingRepositoryImpl.ts';
import {
    CreateOrderGoodsReceipt,
    GetReceivingOrder,
    ListOrderGoodsReceipts,
    ListPurchaseSuppliers,
    ListReceivingOrders,
} from '../../domain/use-cases/inventory/purchase/PurchaseReceivingUseCases.ts';

const repository = new PurchaseReceivingRepositoryImpl();

export const listReceivingOrders = new ListReceivingOrders(repository);
export const getReceivingOrder = new GetReceivingOrder(repository);
export const listOrderGoodsReceipts = new ListOrderGoodsReceipts(repository);
export const createOrderGoodsReceipt = new CreateOrderGoodsReceipt(repository);
export const listPurchaseSuppliers = new ListPurchaseSuppliers(repository);
