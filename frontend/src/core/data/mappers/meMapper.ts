import type {MeResponseDto} from "../dtos/auth/MeResponseDto.ts";
import type {Me} from "../../domain/entities/account/Me.ts";

export const meMapper = (dto: MeResponseDto): Me => ({
    id: dto.id,
    email: dto.email,
    name: dto.name,
    number: dto.number,
    avatar: dto.avatar ?? null,
    has_business: dto.has_business,
    memberships: dto.memberships.map((membership) => ({
        business_id: membership.business_id,
        business_name: membership.business_name,
        role: membership.role,
    })),
    active_business: dto.active_business
        ? {
            id: dto.active_business.id,
            name: dto.active_business.name,
            role: dto.active_business.role,
            slug: dto.active_business.slug,
            logo: dto.active_business.logo ?? null,
            permissions: dto.active_business.permissions ?? [],
        }
        : null,
    meta: {
        needs_onboarding: dto.meta.needs_onboarding,
        business_count: dto.meta.business_count,
    },
});
