export interface Menu {
    id?: number;

    name: string;
    category: string;
    description: string | null;
    sortOrder: number;
    isActive: boolean;

    createdAt?: string;
    updatedAt?: string;
}