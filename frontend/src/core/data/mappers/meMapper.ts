import type {MeResponseDto} from "../dtos/MeResponseDto.ts";
import type {Me} from "../../domain/entities/account/Me.ts";

export const meMapper = (dto: MeResponseDto): Me => {
    return {
        id: dto.id,
        email: dto.email,

        // اگر backend full_name داره ولی تو domain name داری
        name: dto.name,

        number: dto.number,

        has_business: dto.has_business,

        memberships: dto.memberships.map((m) => ({
            business_id: m.business_id,
            business_name: m.business_name,
            role: m.role,
        })),

        active_business: dto.active_business
            ? {
                id: dto.active_business.id,
                name: dto.active_business.name,
                role: dto.active_business.role,
                qr: dto.active_business.qr,

            }
            : null,

        meta: {
            needs_onboarding: dto.meta.needs_onboarding,
            business_count: dto.meta.business_count,
        },
    };
};