import type {UploadOptions, UploadRepository, UploadResult} from "../../../repositories/core/UploadRepository";


export class UploadFile {


    constructor(
        private readonly repository: UploadRepository,
    ) {}



    async execute(
        file: File,

        options?: UploadOptions,

    ): Promise<UploadResult> {


        if (!file) {

            throw new Error(
                "File is required"
            );

        }



        return await this.repository.upload(
            file,
            options,
        );

    }

}