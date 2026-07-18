import type {MembershipDTO} from "./MembershipDTO.ts";
import type {ActiveBusinessDTO} from "../business/ActiveBusinessDTO.ts";
import type {MeMetaDTO} from "./MeMetaDTO.ts";

export interface MeResponseDto {
    id: number;
    email: string;
    name: string;
    number: string;

    has_business: boolean;

    memberships: MembershipDTO[];

    active_business: ActiveBusinessDTO | null;

    meta: MeMetaDTO;
}