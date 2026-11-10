export interface MenuAllergen {
    code: string;
    presence: "contains" | "may_contain";
}

export interface MenuItem {
    id?: number | null;
    menuId?: string;

    name: string;
    recipeId?: string | null;
    productId?: number | null;
    productName?: string | null;
    recipeAllergens?: MenuAllergen[] | null;
    catalogProductAllergens?: MenuAllergen[] | null;
    description: string | null;
    price: number;

    imageUrl: string | null;

    isAvailable: boolean | null;

    createdAt?: string;
    updatedAt?: string;
}