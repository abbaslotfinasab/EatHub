import {useNavigate, useParams} from "react-router-dom";
import {Alert, CircularProgress} from "@mui/material";
import {MenuForm} from "../../components/menu/create/MenuForm";
import {useGetMenuById} from "../../hooks/menu/useGetMenuById.ts";
import {useUpdateMenuWithItems} from "../../hooks/menu/useUpdateMenuWithItems.ts";
import {menuMapper} from "../../../data/mappers/menuMapper.ts";

export const EditMenuPage = () => {
    const navigate = useNavigate();

    const {id} = useParams();

    if (!id) {
        throw new Error("Menu id is required.");
    }

    const {data, isLoading} = useGetMenuById(id);

    const {mutate: updateMenu, isPending} = useUpdateMenuWithItems();

    if (isLoading) {
        return <CircularProgress/>;
    }

    if (!data) {
        return (
            <Alert severity="error">
                منو پیدا نشد.
            </Alert>
        );
    }

    return (
        <MenuForm
            mode="edit"
            loading={isPending}
            initialData={data ? menuMapper.toFormInput(data) : undefined}
            onSubmit={(form) =>
                updateMenu(
                    {
                        id,
                        input: form,
                    },
                    {
                        onSuccess: () => navigate("/menus"),
                    }
                )
            }
        />
    );
};
