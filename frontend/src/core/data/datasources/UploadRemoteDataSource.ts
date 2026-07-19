import type {UploadOptions} from "../../domain/repositories/core/UploadRepository.ts";
import type {UploadFileResponseDTO} from "../dtos/upload/UploadFileResponseDTO";
import {apiClient} from "../http/http-client.ts";


export class UploadRemoteDataSource {


    async upload(
        file: File,
        options?: UploadOptions,
    ): Promise<UploadFileResponseDTO> {


        const formData =
            new FormData();


        formData.append(
            "file",
            file,
        );


        if (options?.folder) {

            formData.append(
                "folder",
                options.folder,
            );

        }


        const {data} = await apiClient.post<UploadFileResponseDTO>(
            "/core/upload/",
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },

                timeout: 120000, // 2 دقیقه


                onUploadProgress(event) {

                    if (!event.total) {
                        return;
                    }


                    const percent =
                        Math.round(
                            (event.loaded / event.total) * 100
                        );


                    options?.onProgress?.(
                        percent,
                    );

                },
            },
        );


        return data;

    }

}