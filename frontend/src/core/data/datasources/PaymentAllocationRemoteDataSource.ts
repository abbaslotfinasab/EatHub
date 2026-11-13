import { apiClient } from '../http/http-client.ts';
import type { CreatePaymentAllocationDTO, PaymentAllocationDTO } from '../dtos/purchase/PaymentAllocationDTO.ts';

export class PaymentAllocationRemoteDataSource {
    async listByPayment(paymentId: string): Promise<PaymentAllocationDTO[]> {
        const { data } = await apiClient.get<PaymentAllocationDTO[]>('/purchase/payment-allocations/', {
            params: { supplier_payment_id: Number(paymentId) },
        });
        return data;
    }

    async create(input: CreatePaymentAllocationDTO): Promise<PaymentAllocationDTO> {
        const { data } = await apiClient.post<PaymentAllocationDTO>('/purchase/payment-allocations/', input);
        return data;
    }
}
