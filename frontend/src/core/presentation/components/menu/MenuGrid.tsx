import {useState} from "react";
import {Alert, Box, Button, Dialog, DialogActions, DialogContent, DialogTitle, Typography} from "@mui/material";
import {useNavigate} from "react-router-dom";
import type {MenuItem} from "../../../domain/entities/product/menu/MenuItem.ts";
import {MenuItemTile} from "./MenuItemTile";
import {useDeleteMenuItem} from "../../hooks/menu/useDeleteMenuItem.ts";

interface Props {
    items: MenuItem[];
}

export const MenuGrid = ({items}: Props) => {
    const navigate = useNavigate();
    const [deleteTarget, setDeleteTarget] = useState<MenuItem | null>(null);
    const {mutate: deleteItem, isPending, isError} = useDeleteMenuItem();

    if (!items.length) {
        return (
            <Box sx={{py: 8, textAlign: "center"}}>
                <Typography variant="h6" sx={{fontWeight: 600}} color="text.secondary">آیتمی پیدا نشد</Typography>
                <Typography variant="body2" color="text.secondary" sx={{mt: 1}}>عبارت جستجو را تغییر دهید</Typography>
            </Box>
        );
    }

    return (
        <>
            <Box sx={{display: "grid", gridTemplateColumns: {xs: "1fr", md: "repeat(2,1fr)"}, gap: 2.5}}>
                {items.map((item) => (
                    <MenuItemTile
                        key={item.id}
                        item={item}
                        onEdit={(selected) => navigate(`/menu-items/${selected.id}/edit`)}
                        onDelete={setDeleteTarget}
                    />
                ))}
            </Box>
            <Dialog open={!!deleteTarget} onClose={() => !isPending && setDeleteTarget(null)}>
                <DialogTitle>حذف آیتم منو</DialogTitle>
                <DialogContent>
                    آیا از حذف «{deleteTarget?.name}» مطمئن هستید؟ این عملیات قابل بازگشت نیست.
                    {isError && <Alert severity="error" sx={{mt: 2}}>حذف آیتم انجام نشد. دوباره تلاش کنید.</Alert>}
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setDeleteTarget(null)} disabled={isPending}>انصراف</Button>
                    <Button color="error" variant="contained" disabled={isPending} onClick={() => {
                        if (deleteTarget?.id == null) return;
                        deleteItem(deleteTarget.id, {onSuccess: () => setDeleteTarget(null)});
                    }}>حذف آیتم</Button>
                </DialogActions>
            </Dialog>
        </>
    );
};
