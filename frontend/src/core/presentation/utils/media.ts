import {API_BASE_URL} from "../../../config/constants.ts";

export function buildMediaUrl(
    path: string,
) {

   if (path.startsWith("http")) {
        return path;
    }

    if (path.startsWith("/media")) {
        return `${API_BASE_URL}${path}`;
    }


    return `${API_BASE_URL}/media/${path}`;

}