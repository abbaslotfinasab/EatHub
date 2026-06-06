import type {CartItem} from "./CartItem.ts";
import type {Cart} from "./Cart.ts";


export interface CartResult{
    cart: Cart;
    items: CartItem[];
}