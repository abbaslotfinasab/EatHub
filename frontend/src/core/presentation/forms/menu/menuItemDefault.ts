import type { MenuFormInput } from "./MenuFormInput";

export const defaultMenuItem: MenuFormInput["items"][number] = {
    name: "",
    recipeId: null,
    productId: null,
    productName: null,
    description: null,
    price: 0,
    imageUrl: null,
    isAvailable: true,
};