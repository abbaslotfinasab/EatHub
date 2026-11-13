import { apiClient } from '../http/http-client.ts';
import type {
    CreateRequisitionPayloadDTO,
    RequisitionDecisionDTO,
    RequisitionOrderSummaryDTO,
    RequisitionReadDTO,
    RequisitionStatusDTO,
} from '../dtos/purchase/PurchaseRequisitionDTO.ts';

export class PurchaseRequisitionRemoteDataSource {
    async list(status?: RequisitionStatusDTO): Promise<RequisitionReadDTO[]> {
        const { data } = await apiClient.get<RequisitionReadDTO[]>('/purchase/requisitions/', {
            params: status ? { status } : undefined,
        });
        return data;
    }

    async get(id: string): Promise<RequisitionReadDTO> {
        const { data } = await apiClient.get<RequisitionReadDTO>(`/purchase/requisitions/${id}/`);
        return data;
    }

    async create(input: CreateRequisitionPayloadDTO): Promise<RequisitionReadDTO> {
        const { data } = await apiClient.post<RequisitionReadDTO>('/purchase/requisitions/', input);
        return data;
    }

    async submit(id: string): Promise<RequisitionReadDTO> {
        const { data } = await apiClient.post<RequisitionReadDTO>(`/purchase/requisitions/${id}/submit/`);
        return data;
    }

    async approve(id: string): Promise<RequisitionReadDTO> {
        const { data } = await apiClient.post<RequisitionReadDTO>(`/purchase/requisitions/${id}/approve/`);
        return data;
    }

    async reject(id: string, reason: string): Promise<RequisitionReadDTO> {
        const { data } = await apiClient.post<RequisitionReadDTO>(`/purchase/requisitions/${id}/reject/`, { reason });
        return data;
    }

    async getOrderSummary(id: string): Promise<RequisitionOrderSummaryDTO> {
        const { data } = await apiClient.get<RequisitionOrderSummaryDTO>(`/purchase/requisitions/${id}/order-summary/`);
        return data;
    }

    async getDecisions(id: string): Promise<RequisitionDecisionDTO[]> {
        const { data } = await apiClient.get<RequisitionDecisionDTO[]>(`/purchase/requisitions/${id}/decisions/`);
        return data;
    }
}
