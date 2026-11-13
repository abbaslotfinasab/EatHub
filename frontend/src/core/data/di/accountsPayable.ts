import { AccountsPayableRepositoryImpl } from '../repositories/AccountsPayableRepositoryImpl.ts';
import { ListAccountsPayables } from '../../domain/use-cases/inventory/purchase/AccountsPayableUseCases.ts';

const repository = new AccountsPayableRepositoryImpl();

export const listAccountsPayables = new ListAccountsPayables(repository);
