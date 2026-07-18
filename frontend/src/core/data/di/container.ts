import {createAuthContainer} from "./auth.container";
import { createCustomerContainer } from "./customer.container.ts";
import {createMenuContainer} from "./menu.container";
import {createOrderContainer} from "./order.container.ts";
import {createUploadContainer} from "./upload.container.ts";

class Container {
    private _auth?: ReturnType<typeof createAuthContainer>;
    private _menu?: ReturnType<typeof createMenuContainer>;
    private _order?: ReturnType<typeof createOrderContainer>;
    private _customer?: ReturnType<typeof createCustomerContainer>;
    private _upload?: ReturnType<typeof createUploadContainer>;



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


    get orderContainer() {
        if (!this._order) {
            this._order = createOrderContainer();
        }

        return this._order;
    }


    get customerContainer() {

        if (!this._customer) {

            this._customer =
                createCustomerContainer();

        }

        return this._customer;

    }

     get uploadContainer() {

        if (!this._upload) {

            this._upload =
                createUploadContainer();

        }

        return this._upload;

    }

}

export const container = new Container();