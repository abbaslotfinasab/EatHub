import {
    Box,
    Card,
    CardActionArea,
    Typography,
} from "@mui/material";

type FoodItemCardProps = {
    item: {
        id: number;
        name: string;
        description?: string;
        price: number;
        imageUrl?: string;
    };
    onClick?: () => void;
};

export const FoodItemCard = ({
    item,
    onClick,
}: FoodItemCardProps) => {
    return (
        <Card
            elevation={0}
            sx={{
                borderRadius: 4,
                border: "1px solid",
                borderColor: "divider",
                overflow: "hidden",
                transition: "all .2s ease",

                "&:hover": {
                    transform: "translateY(-2px)",
                    boxShadow:
                        "0 10px 25px rgba(0,0,0,.06)",
                },
            }}
        >
            <CardActionArea
                onClick={onClick}
                sx={{
                    p: 2,
                }}
            >
                <Box
                    sx={{
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "space-between",
                        gap: 2,
                    }}
                >
                    {/* Content */}
                    <Box
                        sx={{
                            flex: 1,
                            minWidth: 0,
                        }}
                    >
                        <Typography
                            variant="h6"
                            sx={{
                                fontWeight: 700,
                                mb: 0.5,
                                fontSize: 18,
                            }}
                        >
                            {item.name}
                        </Typography>

                        {item.description && (
                            <Typography
                                variant="body2"
                                color="text.secondary"
                                sx={{
                                    mb: 1.5,
                                    display: "-webkit-box",
                                    WebkitLineClamp: 2,
                                    WebkitBoxOrient:
                                        "vertical",
                                    overflow: "hidden",
                                }}
                            >
                                {item.description}
                            </Typography>
                        )}

                        <Typography
                            sx={{
                                fontWeight: 800,
                                fontSize: 16,
                                color: "#10281A",
                            }}
                        >
                            ₼{" "}
                            {item.price.toLocaleString()}
                        </Typography>
                    </Box>

                    {/* Image */}
                    <Box
                        sx={{
                            width: 96,
                            height: 96,
                            flexShrink: 0,
                            borderRadius: 3,
                            overflow: "hidden",
                            backgroundColor: "#f5f5f5",
                        }}
                    >
                        <Box
                            component="img"
                            src={
                                item.imageUrl ||
                                "/placeholder-food.jpg"
                            }
                            alt={item.name}
                            sx={{
                                width: "100%",
                                height: "100%",
                                objectFit: "cover",
                            }}
                        />
                    </Box>
                </Box>
            </CardActionArea>
        </Card>
    );
};