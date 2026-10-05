import {apiClient} from "../http/http-client";
import type {DashboardDTO} from "../dtos/dashboard/DashboardDTO.ts";
import type {DashboardFilters} from "../../domain/objects/filters/DashboardFilters.ts";


export class DashboardRemoteDataSource{


    async getDashboard(filters?: DashboardFilters): Promise<DashboardDTO> {
       const {data} =
            await apiClient.get<DashboardDTO>(
                `/core/dashboard/`,
                {
                    params: {
                        page: filters?.page,
                        page_size: filters?.pageSize,
                    },
                },
            );

        return data;
    }

}
