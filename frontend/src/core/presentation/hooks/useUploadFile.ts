import {useMutation} from "@tanstack/react-query";
import {useState} from "react";
import {container} from "../../data/di/container.ts";
import type {UploadPurpose} from "../../domain/repositories/core/UploadRepository.ts";

interface UploadFileInput {
    file: File;
    folder?: string;
    purpose?: UploadPurpose;
}

export const useUploadFile = () => {
    const {uploadFileUseCase} = container.uploadContainer;
    const [progress, setProgress] = useState(0);

    const mutation = useMutation({
        mutationFn: async (input: UploadFileInput) => {
            setProgress(0);
            return uploadFileUseCase.execute(input.file, {
                folder: input.folder,
                purpose: input.purpose,
                onProgress: setProgress,
            });
        },
        onSuccess: () => setProgress(100),
        onError: () => setProgress(0),
    });

    return {...mutation, progress};
};