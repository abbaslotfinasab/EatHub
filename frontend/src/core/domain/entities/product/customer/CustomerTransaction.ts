// domain/entities/customer/CustomerTransaction.ts

export const CustomerTransactionType = {
    CREDIT: "credit",
    DEBIT: "debit",
    ADJUST: "adjust",
} as const;

export type CustomerTransactionType =
    typeof CustomerTransactionType[keyof typeof CustomerTransactionType];

export interface CustomerTransaction {
    id: string;

    accountId: string;

    orderId?: string | null;

    type: CustomerTransactionType;

    amount: number;

    description?: string | null;

    createdAt?: string;
}