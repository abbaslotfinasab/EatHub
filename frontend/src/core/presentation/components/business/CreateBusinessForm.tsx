import { useState } from "react";
import { Stack, Paper, Typography } from "@mui/material";

import { BusinessLogoUploader } from "./BusinessLogoUploader";
import { BusinessNameField } from "./BusinessNameField";
import { BusinessPhoneField } from "./BusinessPhoneField";
import { BusinessAddressField } from "./BusinessAddressField";
import { CreateBusinessButton } from "./CreateBusinessButton";
import {useCreateBusiness} from "../../hooks/useCreateBusiness.ts";
import {useNavigate} from "react-router-dom";


export interface CreateBusinessFormValues {
  logo: File | null;
  name: string;
  type: string;
  phone: string;
  address: string;
}

export const CreateBusinessForm = () => {
  const { mutateAsync: createBusiness, isPending } = useCreateBusiness();
  const navigate = useNavigate();

  const [values, setValues] = useState<CreateBusinessFormValues>({
    logo: null,
    name: "",
    type: "",
    phone: "",
    address: "",
  });

  const handleChange = <K extends keyof CreateBusinessFormValues>(
    field: K,
    value: CreateBusinessFormValues[K]
  ) => {
    setValues((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const isValid =
    values.name.trim().length > 2 &&
    values.phone.trim().length > 8;

   const handleSubmit = async () => {
    if (!isValid) return;

    try {
      await createBusiness(values);
      navigate("/dashboard"); // 👈 اینجا
    } catch (e) {
      console.error(e);
    }
   };

  return (
    <Paper
      elevation={0}
      sx={{
        p: 3,
        borderRadius: 3,
        border: "1px solid",
        borderColor: "divider",
        maxWidth: 600,
        mx: "auto",
      }}
    >
      <Stack spacing={2}>
        <Typography variant="h6" fontWeight={700}>
          ساخت کسب‌وکار جدید
        </Typography>

        <BusinessLogoUploader
          logo={values.logo}
          onChange={(file) => handleChange("logo", file)}
        />

        <BusinessNameField
          value={values.name}
          onChange={(val) => handleChange("name", val)}
        />

        <BusinessPhoneField
          value={values.phone}
          onChange={(val) => handleChange("phone", val)}
        />

        <BusinessAddressField
          value={values.address}
          onChange={(val) => handleChange("address", val)}
        />

        <CreateBusinessButton
          onClick={handleSubmit}
          isLoading={isPending}
          disabled={!isValid}
        />
      </Stack>
    </Paper>
  );
};