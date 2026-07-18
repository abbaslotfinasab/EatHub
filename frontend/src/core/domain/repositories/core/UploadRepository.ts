export interface UploadRepository {

    upload(
        file: File,
        options?: UploadOptions,
    ): Promise<UploadResult>;

}


export interface UploadOptions {

    folder?: string;

    onProgress?: (
        progress: number
    ) => void;

}



export interface UploadResult {

    url: string;

    path: string;

    filename: string;

    size: number;

    contentType: string;

}