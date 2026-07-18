import type {Menu} from "./Menu.ts";
import type {MenuItem} from "./MenuItem.ts";


export interface MenuWithItems {
    menu: Menu;
    items: MenuItem[];
}