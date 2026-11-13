import { SupplierPaymentRepositoryImpl } from '../repositories/SupplierPaymentRepositoryImpl.ts';
import {
    CreateSupplierPayment,
    ListSupplierPayments,
} from '../../domain/use-cases/inventory/purchase/SupplierPaymentUseCases.ts';

const repository = new SupplierPaymentRepositoryImpl();

export const listSupplierPayments = new ListSupplierPayments(repository);
export const createSupplierPayment = new CreateSupplierPayment(repository);
