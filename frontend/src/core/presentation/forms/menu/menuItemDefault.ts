// menuItemDefault.ts

import type { MenuFormInput } from "./MenuFormInput";


export const defaultMenuItem: MenuFormInput["items"][number] = {
    name: "",
    recipeId: null,
    description: null,
    price: 0,
    imageUrl: null,
    isAvailable: true,
};