import {createAuthContainer} from "./auth.container.ts";

class Container {
    private _auth?: ReturnType<typeof createAuthContainer>;

    get authContainer() {
        if (!this._auth) {
            this._auth = createAuthContainer();
        }
        return this._auth;
    }
}

export const container = new Container();