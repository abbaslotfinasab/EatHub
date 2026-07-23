import {apiClient} from "../http/http-client";
import type {DashboardDTO} from "../dtos/dashboard/DashboardDTO.ts";


export class DashboardRemoteDataSource{


    async getDashboard(): Promise<DashboardDTO> {
       const {data} =
            await apiClient.get<DashboardDTO>(
                `/core/dashboard/`,
            );

        return data;
    }

}