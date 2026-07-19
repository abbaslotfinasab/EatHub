import {BASE_URL} from "../../../config/constants.ts";

export function buildMediaUrl(
    path: string,
) {

   if (path.startsWith("http")) {
        return path;
    }

    if (path.startsWith("/media")) {
        return `${BASE_URL}${path}`;
    }


    return `${BASE_URL}/media/${path}`;

}