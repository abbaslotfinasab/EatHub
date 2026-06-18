import type {ActiveBusiness} from "./ActiveBusiness.ts";
import type {Membership} from "./Membership.ts";
import type {MeMeta} from "./MeMeta.ts";

export interface Me {
    id: number;
    email: string;
    name: string;
    number: string;

    has_business: boolean;

    memberships: Membership[];

    active_business: ActiveBusiness | null;

    meta: MeMeta;
}