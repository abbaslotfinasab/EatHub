import {Search, FilterList, Add} from "@mui/icons-material";
import {
    Box,
    Button,
    IconButton,
    InputAdornment,
    OutlinedInput,
    Stack,
    Tooltip,
} from "@mui/material";

interface CustomersToolbarProps {
    search: string;

    onSearchChange(value: string): void;

    onFilterClick(): void;

    onCreateClick(): void;
}

export function CustomersToolbar({
                                     search,
                                     onSearchChange,
                                     onFilterClick,
                                     onCreateClick,
                                 }: CustomersToolbarProps) {
    return (
        <Stack
            sx={{
                flexDirection: {
                    xs: "column",
                    md: "row",
                },
                gap: 2,
                justifyContent: "space-between",
                alignItems: {
                    xs: "stretch",
                    md: "center",
                },
            }}
        >
            <OutlinedInput
                fullWidth
                value={search}
                placeholder="جستجوی مشتری..."
                onChange={(event) => onSearchChange(event.target.value)}
                startAdornment={
                    <InputAdornment position="start">
                        <Search fontSize="small"/>
                    </InputAdornment>
                }
                sx={{
                    maxWidth: 420,
                }}
            />

            <Box
                sx={{
                    display: "flex",
                    gap: 1,
                    justifyContent: "flex-end",
                }}
            >
                <Tooltip title="فیلتر">
                    <IconButton
                        onClick={onFilterClick}
                        sx={{
                            border: 1,
                            borderColor: "divider",
                            borderRadius: 2,
                        }}
                    >
                        <FilterList/>
                    </IconButton>
                </Tooltip>

                <Button
                    variant="contained"
                    startIcon={<Add/>}
                    onClick={onCreateClick}
                >
                    مشتری جدید
                </Button>
            </Box>
        </Stack>
    );
}