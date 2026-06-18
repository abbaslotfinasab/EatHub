
export interface OrderFilters {
    customerId?: string;
    tableId?: string;
    statusId?: string;
    fromDate?: string;      // ISO date (YYYY-MM-DD)
    toDate?: string;
    orderType?: 'dine_in' | 'takeaway' | 'delivery';
    // paymentMethod?: PaymentMethodType;
    paymentStatus?: 'pending' | 'paid' | 'failed' | 'refunded';
    minTotal?: number;
    maxTotal?: number;
}
