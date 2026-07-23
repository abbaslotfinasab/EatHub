import type {
    ActivityDTO,
} from "../dtos/dashboard/ActivityDTO";


import type {Activity, ActivityAction} from "../../domain/entities/core/dashboard/Activity.ts";


export const activityMapper = {

    // =====================================================
    // DTO -> DOMAIN
    // =====================================================

    toDomain(
        dto: ActivityDTO,
    ): Activity {

        return {

            id: dto.id,

            title: dto.title,

            description:
                dto.description ??
                undefined,

            user:
                dto.user ??
                undefined,

             action:
                dto.action as ActivityAction,


            createdAt:
                dto.created_at,
        };
    },


    // =====================================================
    // DTO LIST -> DOMAIN LIST
    // =====================================================

    toDomainList(
        dtos: ActivityDTO[],
    ): Activity[] {

        return dtos.map(
            activityMapper.toDomain,
        );
    },

};