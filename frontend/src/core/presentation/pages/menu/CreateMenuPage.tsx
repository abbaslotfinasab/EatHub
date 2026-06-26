// src/presentation/pages/CreateMenuPage.tsx

import {useNavigate} from "react-router-dom";

import {useCreateMenuWithItems} from "../../hooks/useCreateMenuWithItems";
import {MenuForm} from "../../components/menu/create/MenuForm.tsx";

export const CreateMenuPage = () => {
    const navigate = useNavigate();

    const { mutate: createMenu, isPending } = useCreateMenuWithItems();

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