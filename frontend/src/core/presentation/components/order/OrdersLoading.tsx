import {
    Paper,
    Skeleton,
    Stack,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
} from "@mui/material";

const StatsSkeleton = () => (
    <Stack
        direction={{xs: "column", md: "row"}}
        spacing={2}
    >
        {Array.from({length: 4}).map((_, index) => (
            <Paper
                key={index}
                elevation={0}
                sx={{
                    flex: 1,
                    p: 2.5,
                    borderRadius: 3,
                    border: "1px solid",
                    borderColor: "divider",
                }}
            >
                <Stack spacing={2}>
                    <Skeleton
                        variant="circular"
                        width={36}
                        height={36}
                    />

                    <Skeleton
                        variant="text"
                        width="40%"
                        height={40}
                    />

                    <Skeleton
                        variant="text"
                        width="60%"
                    />
                </Stack>
            </Paper>
        ))}
    </Stack>
);

const ToolbarSkeleton = () => (
    <Stack spacing={2}>
        <Stack
            sx={{
                flexDirection: "row",
                justifyContent: "space-between",
                alignItems: "center",
            }}
        >
            <Skeleton
                variant="rounded"
                width={320}
                height={40}
            />

            <Skeleton
                variant="circular"
                width={40}
                height={40}
            />
        </Stack>

        <Stack
            direction="row"
            spacing={1}
        >
            {Array.from({length: 6}).map((_, index) => (
                <Skeleton
                    key={index}
                    variant="rounded"
                    width={90}
                    height={32}
                />
            ))}
        </Stack>
    </Stack>
);

const TableSkeleton = () => (
    <TableContainer
        component={Paper}
        elevation={0}
        sx={{
            borderRadius: 3,
            border: "1px solid",
            borderColor: "divider",
        }}
    >
        <Table>

            <TableHead>
                <TableRow>
                    {Array.from({length: 9}).map((_, index) => (
                        <TableCell key={index}>
                            <Skeleton
                                width="70%"
                            />
                        </TableCell>
                    ))}
                </TableRow>
            </TableHead>

            <TableBody>

                {Array.from({length: 8}).map((_, row) => (
                    <TableRow key={row}>
                        {Array.from({length: 9}).map((_, cell) => (
                            <TableCell key={cell}>
                                <Skeleton
                                    height={28}
                                />
                            </TableCell>
                        ))}
                    </TableRow>
                ))}

            </TableBody>

        </Table>
    </TableContainer>
);

export const OrdersLoading = () => {
    return (
        <Stack spacing={3}>
            <StatsSkeleton/>

            <ToolbarSkeleton/>

            <TableSkeleton/>
        </Stack>
    );
};