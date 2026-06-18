import Chip from "@mui/material/Chip";

interface Props {
    status: string;
}

export const OrderStatusChip = ({
                                    status,
                                }: Props) => {
    const config = {
        pending: {
            label: "در انتظار",
            color: "#F59E0B",
        },

        preparing: {
            label: "درحال آماده سازی",
            color: "#3B82F6",
        },

        ready: {
            label: "آماده تحویل",
            color: "#8B5CF6",
        },

        completed: {
            label: "تکمیل شده",
            color: "#22C55E",
        },

        cancelled: {
            label: "لغو شده",
            color: "#EF4444",
        },
    };

    const item =
        config[status as keyof typeof config];

    return (
        <Chip
            label={item.label}
            size="small"
            sx={{
                bgcolor: `${item.color}20`,
                color: item.color,
                fontWeight: 600,
            }}
        />
    );
};