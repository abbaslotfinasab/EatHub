// core/application/use-cases/table/GetAllTables.ts
import type { TableRepository } from '../../../repositories/product/TableRepository';
import type { Table } from '../../../entities/product/Table';
import type {TableFilters} from "../../../objects/filters/TableFilters.ts";

export class GetAllTables {
    constructor(private tableRepository: TableRepository) {}

    async execute(filters?: TableFilters): Promise<Table[]> {
        return this.tableRepository.findAll(filters);
    }
}