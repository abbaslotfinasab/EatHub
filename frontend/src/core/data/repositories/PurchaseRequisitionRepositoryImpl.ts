import type { PurchaseRequisitionRepository } from '../../domain/repositories/inventory/PurchaseRequisitionRepository.ts';
import type {
    PurchaseRequisition,
    RequisitionDecision,
    RequisitionInput,
    RequisitionOrderSummary,
    RequisitionStatus,
} from '../../domain/entities/inventory/PurchaseRequisition.ts';
import type {
    CreateRequisitionPayloadDTO,
    RequisitionDecisionDTO,
    RequisitionOrderSummaryDTO,
    RequisitionReadDTO,
    RequisitionStatusDTO,
} from '../dtos/purchase/PurchaseRequisitionDTO.ts';
import { PurchaseRequisitionRemoteDataSource } from '../datasources/PurchaseRequisitionRemoteDataSource.ts';

const mapRequisition = (dto: RequisitionReadDTO): PurchaseRequisition => ({
    id: String(dto.id),
    businessId: String(dto.business_id),
    requestedById: String(dto.requested_by_id),
    status: dto.status,
    reason: dto.reason,
    items: dto.items.map((item) => ({
        ingredientId: String(item.ingredient_id),
        quantity: item.quantity,
        note: item.note,
    })),
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
});

const mapSummary = (dto: RequisitionOrderSummaryDTO): RequisitionOrderSummary => ({
    requisitionId: String(dto.requisition_id),
    businessId: String(dto.business_id),
    status: dto.status,
    items: dto.items.map((item) => ({
        ingredientId: String(item.ingredient_id),
        requestedQuantity: item.requested_quantity,
        orderedQuantity: item.ordered_quantity,
        remainingQuantity: item.remaining_quantity,
    })),
});

const mapDecision = (dto: RequisitionDecisionDTO): RequisitionDecision => ({
    decision: dto.decision,
    actorId: String(dto.actor_id),
    actorName: dto.actor_name,
    decidedAt: dto.decided_at,
    previousStatus: dto.previous_status,
    resultingStatus: dto.resulting_status,
    rejectionReason: dto.rejection_reason,
});

const toCreateDTO = (input: RequisitionInput): CreateRequisitionPayloadDTO => ({
    reason: input.reason,
    items: input.items.map((item) => ({
        ingredient_id: Number(item.ingredientId),
        quantity: item.quantity,
        note: item.note,
    })),
});

export class PurchaseRequisitionRepositoryImpl implements PurchaseRequisitionRepository {
    constructor(private readonly remote = new PurchaseRequisitionRemoteDataSource()) {}

    async list(status?: RequisitionStatus): Promise<PurchaseRequisition[]> {
        return (await this.remote.list(status as RequisitionStatusDTO | undefined)).map(mapRequisition);
    }

    async get(id: string): Promise<PurchaseRequisition> {
        return mapRequisition(await this.remote.get(id));
    }

    async create(input: RequisitionInput): Promise<PurchaseRequisition> {
        return mapRequisition(await this.remote.create(toCreateDTO(input)));
    }

    async submit(id: string): Promise<PurchaseRequisition> {
        return mapRequisition(await this.remote.submit(id));
    }

    async approve(id: string): Promise<PurchaseRequisition> {
        return mapRequisition(await this.remote.approve(id));
    }

    async reject(id: string, reason: string): Promise<PurchaseRequisition> {
        return mapRequisition(await this.remote.reject(id, reason));
    }

    async getOrderSummary(id: string): Promise<RequisitionOrderSummary> {
        return mapSummary(await this.remote.getOrderSummary(id));
    }

    async getDecisions(id: string): Promise<RequisitionDecision[]> {
        return (await this.remote.getDecisions(id)).map(mapDecision);
    }
}
