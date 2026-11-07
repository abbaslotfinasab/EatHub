import {useEffect, useState} from "react";
import {apiClient} from "../../data/http/http-client.ts";

interface BusinessProfileResponse {
    logo?: string | null;
}

export const useBusinessLogo = (businessId: number | null) => {
    const [logo, setLogo] = useState<string | null>(null);

    useEffect(() => {
        let active = true;

        const loadLogo = async () => {
            if (!businessId) {
                setLogo(null);
                return;
            }

            try {
                const {data} = await apiClient.get<BusinessProfileResponse>("/accounts/business/profile/");
                if (active) setLogo(data.logo ?? null);
            } catch {
                if (active) setLogo(null);
            }
        };

        void loadLogo();
        window.addEventListener("business-profile-updated", loadLogo);

        return () => {
            active = false;
            window.removeEventListener("business-profile-updated", loadLogo);
        };
    }, [businessId]);

    return logo;
};
