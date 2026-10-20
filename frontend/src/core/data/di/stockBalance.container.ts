import { StockBalanceRemoteDataSource } from "../datasources/StockBalanceRemoteDataSource";
import { StockBalanceRepositoryImpl } from "../repositories/StockBalanceRepositoryImpl";
import { ListStockBalances } from "../../domain/use-cases/inventory/stock-balance/ListStockBalances";

const remote = new StockBalanceRemoteDataSource();
const repository = new StockBalanceRepositoryImpl(remote);

export const listStockBalancesUseCase = new ListStockBalances(repository);
