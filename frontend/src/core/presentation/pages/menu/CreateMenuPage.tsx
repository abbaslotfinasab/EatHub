// src/presentation/pages/CreateMenuPage.tsx

import {useNavigate} from "react-router-dom";

import {MenuForm} from "../../components/menu/create/MenuForm.tsx";
import {useCreateMenu} from "../../hooks/menu/useCreateMenu.ts";

export const CreateMenuPage = () => {
    const navigate = useNavigate();

    const { mutate: createMenu, isPending } = useCreateMenu();

    return (
        <MenuForm
            mode="create"
            loading={isPending}
            onSubmit={(data) =>
                createMenu(data, {
                    onSuccess: () => navigate("/menus"),
                })
            }
        />
    );
};