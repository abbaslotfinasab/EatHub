import {
    Box,
    Button,
    Divider,
    FormControl,
    InputLabel,
    MenuItem,
    Popover,
    Select,
    Stack,
    Typography,
} from "@mui/material";
import type {MenuItemsFilter, MenuOrdering, MenuStatusFilter } from "../../../domain/objects/filters/MenuFilters";


interface MenuFilterPopoverProps {
    anchorEl: HTMLElement | null;

    open: boolean;

    status: MenuStatusFilter;

    items: MenuItemsFilter;

    ordering: MenuOrdering;

    onClose(): void;

    onStatusChange(
        value: MenuStatusFilter,
    ): void;

    onItemsChange(
        value: MenuItemsFilter,
    ): void;

    onOrderingChange(
        value: MenuOrdering,
    ): void;

    onClear(): void;
}

export function MenuFilterPopover({
    anchorEl,
    open,
    status,
    items,
    ordering,
    onClose,
    onStatusChange,
    onItemsChange,
    onOrderingChange,
    onClear,
}: MenuFilterPopoverProps) {

    return (
        <Popover
            open={open}
            anchorEl={anchorEl}
            onClose={onClose}
            anchorOrigin={{
                vertical: "bottom",
                horizontal: "right",
            }}
            transformOrigin={{
                vertical: "top",
                horizontal: "right",
            }}
            slotProps={{
                paper: {
                    sx: {
                        width: 340,
                        borderRadius: 1,
                        p: 3,
                        mt: 1,
                    },
                },
            }}
        >
            <Stack spacing={3}>

                <Typography
                    variant="h6"
                    sx={{
                        fontWeight: 700,
                    }}
                >
                    فیلتر منوها
                </Typography>

                <Divider />

                <FormControl fullWidth>

                    <InputLabel>
                        وضعیت منو
                    </InputLabel>

                    <Select
                        label="وضعیت منو"
                        value={status}
                        onChange={(e) =>
                            onStatusChange(
                                e.target.value as MenuStatusFilter,
                            )
                        }
                    >
                        <MenuItem value="ALL">
                            همه
                        </MenuItem>

                        <MenuItem value="ACTIVE">
                            فعال
                        </MenuItem>

                        <MenuItem value="INACTIVE">
                            غیرفعال
                        </MenuItem>

                    </Select>

                </FormControl>

                <FormControl fullWidth>

                    <InputLabel>
                        وضعیت آیتم‌ها
                    </InputLabel>

                    <Select
                        label="وضعیت آیتم‌ها"
                        value={items}
                        onChange={(e) =>
                            onItemsChange(
                                e.target.value as MenuItemsFilter,
                            )
                        }
                    >
                        <MenuItem value="ALL">
                            همه
                        </MenuItem>

                        <MenuItem value="HAS_ITEMS">
                            دارای آیتم
                        </MenuItem>

                        <MenuItem value="EMPTY">
                            بدون آیتم
                        </MenuItem>

                    </Select>

                </FormControl>

                <FormControl fullWidth>

                    <InputLabel>
                        مرتب‌سازی
                    </InputLabel>

                    <Select
                        label="مرتب‌سازی"
                        value={ordering}
                        onChange={(e) =>
                            onOrderingChange(
                                e.target.value as MenuOrdering,
                            )
                        }
                    >
                        <MenuItem value="-created_at">
                            جدیدترین
                        </MenuItem>

                        <MenuItem value="created_at">
                            قدیمی‌ترین
                        </MenuItem>

                        <MenuItem value="name">
                            نام منو
                        </MenuItem>

                        <MenuItem value="sort_order">
                            ترتیب نمایش
                        </MenuItem>

                    </Select>

                </FormControl>

                <Divider />

                <Box
                    sx={{
                        display: "flex",
                        gap: 1,
                    }}
                >
                    <Button
                        fullWidth
                        variant="outlined"
                        color="inherit"
                        onClick={onClear}
                    >
                        حذف فیلترها
                    </Button>

                    <Button
                        fullWidth
                        variant="contained"
                        onClick={onClose}
                    >
                        اعمال
                    </Button>
                </Box>

            </Stack>
        </Popover>
    );
}