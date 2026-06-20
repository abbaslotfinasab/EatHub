// src/features/business/presentation/components/CreateBusinessButton.tsx

import Button from "@mui/material/Button";

interface Props {
  onClick: () => void;
  isLoading?: boolean;
  disabled?: boolean;
}

export const CreateBusinessButton = ({
  onClick,
}: Props) => {
  return (
    <Button
      fullWidth
      size="large"
      variant="contained"
      disableElevation
      onClick={onClick}
      type="submit"

      sx={{
        mt: 2,
        height: 56,
        borderRadius: 4,
        fontSize: 16,
        fontWeight: 700,
        textTransform: "none",
      }}
    >
      ایجاد کسب‌وکار
    </Button>
  );
};