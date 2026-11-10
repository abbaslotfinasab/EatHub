export interface MenuItem {
    id?: number | null;
    menuId?: string;

    name: string;
    recipeId?: string | null;
    productId?: number | null;
    productName?: string | null;
    description: string | null;
    price: number;

    imageUrl: string | null;

    isAvailable: boolean | null;

    createdAt?: string;
    updatedAt?: string;
}