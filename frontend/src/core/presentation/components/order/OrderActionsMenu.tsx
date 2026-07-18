import VisibilityRoundedIcon from "@mui/icons-material/VisibilityRounded";
import AutorenewRoundedIcon from "@mui/icons-material/AutorenewRounded";
import PrintRoundedIcon from "@mui/icons-material/PrintRounded";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";

import {
    Divider,
    ListItemIcon,
    ListItemText,
    Menu,
    MenuItem,
} from "@mui/material";
import EditRoundedIcon from "@mui/icons-material/EditRounded";

interface OrderActionsMenuProps {
    anchorEl: HTMLElement | null;
    open: boolean;

    onClose: () => void;

    onView?: () => void;
    onChangeStatus?: () => void;
    onPrint?: () => void;
    onEdit?: () => void;
    onDelete?: () => void;
}

export const OrderActionsMenu = ({
                                     anchorEl,
                                     open,
                                     onClose,
                                     onView,
                                     onChangeStatus,
                                     onPrint,
                                     onEdit,
                                     onDelete,
                                 }: OrderActionsMenuProps) => {
    const handleAction = (callback?: () => void) => {
        onClose();
        callback?.();
    };

    return (
        <Menu
            anchorEl={anchorEl}
            open={open}
            onClose={onClose}
            anchorOrigin={{
                vertical: "bottom",
                horizontal: "left",
            }}
            transformOrigin={{
                vertical: "top",
                horizontal: "left",
            }}
            slotProps={{
                paper: {
                    elevation: 0,
                    sx: {
                        minWidth: 220,
                        borderRadius: 3,
                        border: "1px solid",
                        borderColor: "divider",
                        mt: 1,
                    },
                },
            }}
        >
            <MenuItem onClick={() => handleAction(onView)}>
                <ListItemIcon>
                    <VisibilityRoundedIcon fontSize="small"/>
                </ListItemIcon>

                <ListItemText>
                    مشاهده جزئیات
                </ListItemText>
            </MenuItem>

            <MenuItem onClick={() => handleAction(onChangeStatus)}>
                <ListItemIcon>
                    <AutorenewRoundedIcon fontSize="small"/>
                </ListItemIcon>

                <ListItemText>
                    تغییر وضعیت
                </ListItemText>
            </MenuItem>

            <MenuItem onClick={() => handleAction(onPrint)}>
                <ListItemIcon>
                    <PrintRoundedIcon fontSize="small"/>
                </ListItemIcon>

                <ListItemText>
                    چاپ فاکتور
                </ListItemText>
            </MenuItem>

            <Divider/>


            <MenuItem
                onClick={() => handleAction(onEdit)}
                sx={{
                    color: "",
                }}
            >
                <ListItemIcon
                    sx={{
                        color: "inherit",
                    }}
                >
                    <EditRoundedIcon fontSize="small"/>

                </ListItemIcon>

                <ListItemText>
                    ویرایش سفارش
                </ListItemText>
            </MenuItem>



            <MenuItem
                onClick={() => handleAction(onDelete)}
                sx={{
                    color: "error.main",
                }}
            >
                <ListItemIcon
                    sx={{
                        color: "inherit",
                    }}
                >
                    <DeleteOutlineRoundedIcon fontSize="small"/>
                </ListItemIcon>

                <ListItemText>
                    حذف سفارش
                </ListItemText>
            </MenuItem>
        </Menu>
    );
};