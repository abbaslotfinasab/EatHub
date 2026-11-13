import { PaymentAllocationRepositoryImpl } from '../repositories/PaymentAllocationRepositoryImpl.ts';
import { CreatePaymentAllocation, ListPaymentAllocations } from '../../domain/use-cases/inventory/purchase/PaymentAllocationUseCases.ts';

const repository = new PaymentAllocationRepositoryImpl();

export const listPaymentAllocations = new ListPaymentAllocations(repository);
export const createPaymentAllocation = new CreatePaymentAllocation(repository);
