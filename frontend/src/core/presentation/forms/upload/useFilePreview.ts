import {useEffect, useMemo} from "react";
import {buildMediaUrl} from "../../utils/media.ts";

export function useFilePreview(
    file?: File | null,
    path?: string | null,
) {

    const preview = useMemo(() => {

        if (file) {
            return {
                type: "blob",
                url: URL.createObjectURL(file),
            };
        }

        if (path) {
            return {
                type: "media",
                url: buildMediaUrl(path),
            };
        }

        return null;

    }, [file, path]);


    useEffect(() => {

        return () => {

            if (
                preview?.type === "blob"
            ) {
                URL.revokeObjectURL(
                    preview.url
                );
            }

        };

    }, [preview]);


    return preview;
}