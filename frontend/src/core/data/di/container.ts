import {createAuthContainer} from "./auth.container";
import {createCustomerContainer} from "./customer.container.ts";
import {createMenuContainer} from "./menu.container";
import {createOrderContainer} from "./order.container.ts";
import {createUploadContainer} from "./upload.container.ts";
import {createDashboardContainer} from "./dashboard.container.ts";

class Container {
    private _auth?: ReturnType<typeof createAuthContainer>;
    private _menu?: ReturnType<typeof createMenuContainer>;
    private _order?: ReturnType<typeof createOrderContainer>;
    private _customer?: ReturnType<typeof createCustomerContainer>;
    private _upload?: ReturnType<typeof createUploadContainer>;
    private _dashboard?: ReturnType<typeof createDashboardContainer>;


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

    get dashboardContainer() {

        if (!this._dashboard) {

            this._dashboard =
                createDashboardContainer();

        }

        return this._dashboard;

    }

}

export const container = new Container();