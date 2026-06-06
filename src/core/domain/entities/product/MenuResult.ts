import type {Menu} from "./Menu.ts";
import type {MenuItem} from "./MenuItem.ts";


export interface MenuResult{
    menu: Menu;
    items: MenuItem[];
}