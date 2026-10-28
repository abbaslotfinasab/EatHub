import type {OrderRepository} from "../../domain/repositories/product/OrderRepository.ts";
import type {OrderWithItems} from "../../domain/entities/product/order/OrderWithItems.ts";


import {OrderRemoteDataSource} from "../datasources/OrderRemoteDataSource";
import {orderMapper} from "../mappers/orderMapper";
import type {UpdateOrderStatusInput} from "../../domain/entities/product/order/UpdateOrderStatusInput.ts";
import type {UpdateOrderStatusDTO} from "../dtos/order/UpdateOrderStatusDTO.ts";
import type {OrderFilters} from "../../domain/objects/filters/OrderFilters.ts";
import type {PaginatedResult} from "../../domain/objects/PaginatedResult.ts";
import type {RefundOrderInput, RefundOrderResult} from "../../domain/entities/product/order/RefundOrderInput.ts";
import type {OrderRefundDTO} from "../dtos/order/OrderRefundDTO.ts";
import type {
    OrderConsumptionRequirementsDTO,
    RecordOrderConsumptionDTO,
    RecordOrderConsumptionResultDTO,
} from "../dtos/order/OrderInventoryConsumptionDTO.ts";
import type {
    OrderConsumptionRequirements,
    RecordOrderConsumptionInput,
    RecordOrderConsumptionResult,
} from "../../domain/entities/product/order/OrderInventoryConsumption.ts";

export class OrderRepositoryImpl implements OrderRepository {

    constructor(
        private remote: OrderRemoteDataSource,
    ) {
    }

    // =========================
    // CREATE
    // =========================

    async create(input: OrderWithItems): Promise<void> {
        const dto = orderMapper.toCreateDTO(input);

        await this.remote.createOrder(dto);
    }

    // =========================
    // READ
    // =========================

    async findAll(
        filters?: OrderFilters,
    ): Promise<PaginatedResult<OrderWithItems>> {
        const data = await this.remote.getOrders(filters);

        return {
            count: data.count,
            next: data.next,
            previous: data.previous,
            results: data.results.map(orderMapper.toDomain),
        };
    }

    async findById(id: string): Promise<OrderWithItems> {
        const data = await this.remote.getOrderById(id);

        return orderMapper.toDomain(data);
    }

    // =========================
    // UPDATE
    // =========================

    async update(id: string, order: OrderWithItems): Promise<void> {
        if (!id) {
            throw new Error("Order id is required");
        }

        const dto = orderMapper.toUpdateDTO(order);

        await this.remote.updateOrder(
            id,
            dto,
        );
    }

    // =========================
    // DELETE
    // =========================

    async delete(id: string): Promise<void> {
        await this.remote.deleteOrder(id);
    }

    async updateStatus(
        input: UpdateOrderStatusInput,
    ): Promise<void> {


        const dto: UpdateOrderStatusDTO = {

            status: input.status,

            payment_status:
            input.paymentStatus,

            payment_method:
            input.paymentMethod,

        };


        await this.remote.updateStatus(
            input.orderId,
            dto,
        );
    }

    async refund(input: RefundOrderInput): Promise<RefundOrderResult> {
        const dto: OrderRefundDTO = {
            idempotency_key: input.idempotencyKey,
            reason: input.reason,
            reference: input.reference,
            amount: input.amount?.toFixed(2),
            confirm_external_refund: input.confirmExternalRefund,
        };
        return this.remote.refundOrder(input.orderId, dto);
    }

    async getRefund(orderId: string): Promise<RefundOrderResult> {
        return this.remote.getOrderRefund(orderId);
    }

    async getConsumptionRequirements(orderId: string): Promise<OrderConsumptionRequirements> {
        const data: OrderConsumptionRequirementsDTO = await this.remote.getConsumptionRequirements(orderId);
        return {
            orderId: data.order_id,
            requirements: data.requirements.map((row) => ({
                requirementId: row.requirement_id,
                orderItemId: row.order_item_id,
                menuItemName: row.menu_item_name,
                ingredientId: row.ingredient_id,
                ingredientName: row.ingredient_name,
                standardQuantity: row.standard_quantity,
                actualQuantity: row.actual_quantity,
                unit: row.unit,
                hasActualRecord: row.has_actual_record,
            })),
        };
    }

    async recordConsumption(
        input: RecordOrderConsumptionInput,
    ): Promise<RecordOrderConsumptionResult> {
        const payload: RecordOrderConsumptionDTO = {
            idempotency_key: input.idempotencyKey,
            lines: input.lines.map((line) => ({
                requirement_id: line.requirementId,
                quantity: line.quantity,
                unit: line.unit,
            })),
        };
        const data: RecordOrderConsumptionResultDTO = await this.remote.recordConsumption(
            input.orderId,
            payload,
        );
        return {
            id: data.id,
            orderId: data.order_id,
            idempotencyKey: data.idempotency_key,
            createdAt: data.created_at,
            inventoryOperationId: data.inventory_operation_id,
            lines: data.lines.map((line) => ({
                requirementId: line.requirement_id,
                orderItemId: line.order_item_id,
                ingredientId: line.ingredient_id,
                actualQuantity: line.actual_quantity,
                unit: line.unit,
                movementId: line.movement_id,
            })),
        };
    }
}
