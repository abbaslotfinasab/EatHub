import { createAuthContainer } from "./auth.container";
import { createMenuContainer } from "./menu.container";

class Container {
    private _auth?: ReturnType<typeof createAuthContainer>;
    private _menu?: ReturnType<typeof createMenuContainer>;

    get authContainer() {
        if (!this._auth) {
            this._auth = createAuthContainer();
        }
        return this._auth;
    }

    get menuContainer() {
        if (!this._menu) {
            this._menu = createMenuContainer();
        }
        return this._menu;
    }
}

export const container = new Container();