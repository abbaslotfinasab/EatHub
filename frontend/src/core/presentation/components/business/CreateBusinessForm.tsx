import {useState} from "react";
import {Stack, Paper, Typography, Alert} from "@mui/material";
import {BusinessLogoUploader} from "./BusinessLogoUploader";
import {BusinessNameField} from "./BusinessNameField";
import {BusinessPhoneField} from "./BusinessPhoneField";
import {BusinessAddressField} from "./BusinessAddressField";
import {CreateBusinessButton} from "./CreateBusinessButton";
import {useCreateBusiness} from "../../hooks/useCreateBusiness.ts";
import {useUploadFile} from "../../hooks/useUploadFile.ts";
import {useFilePreview} from "../../forms/upload/useFilePreview.ts";
import {useNavigate} from "react-router-dom";

export interface CreateBusinessFormValues {
  logo: File | null;
  name: string;
  type: string;
  phone: string;
  address: string;
}

export const CreateBusinessForm = () => {
  const {mutateAsync: createBusiness, isPending} = useCreateBusiness();
  const {mutateAsync: uploadFile, isPending: isUploading, progress} = useUploadFile();
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [values, setValues] = useState<CreateBusinessFormValues>({
    logo: null, name: "", type: "", phone: "", address: "",
  });
  const preview = useFilePreview(values.logo);

  const handleChange = <K extends keyof CreateBusinessFormValues>(
    field: K, value: CreateBusinessFormValues[K],
  ) => setValues(prev => ({...prev, [field]: value}));

  const isValid = values.name.trim().length > 2 && values.phone.trim().length > 8;

  const handleSubmit = async () => {
    if (!isValid || isPending || isUploading) return;
    try {
      setSubmitError(null);
      const uploaded = values.logo
        ? await uploadFile({file: values.logo, purpose: "business_logo"})
        : null;
      await createBusiness({
        name: values.name.trim(),
        phone: values.phone.trim(),
        address: values.address.trim(),
        logoUrl: uploaded?.path ?? null,
      });
      navigate("/dashboard");
    } catch (error) {
      console.error(error);
      setSubmitError("ایجاد کسب‌وکار انجام نشد. اطلاعات را بررسی کنید و دوباره تلاش کنید.");
    }
  };

  return (
    <Paper elevation={0} sx={{p: 3, borderRadius: 3, border: "1px solid", borderColor: "divider", maxWidth: 600, mx: "auto"}}>
      <Stack spacing={2}>
        {submitError && <Alert severity="error">{submitError}</Alert>}
        <Typography sx={{fontWeight: 700}}>ساخت کسب‌وکار جدید</Typography>
        <BusinessLogoUploader
          logo={values.logo}
          previewUrl={preview?.url}
          onChange={file => handleChange("logo", file)}
        />
        {isUploading && <Typography variant="caption">در حال آپلود لوگو… {progress}%</Typography>}
        <BusinessNameField value={values.name} onChange={val => handleChange("name", val)}/>
        <BusinessPhoneField value={values.phone} onChange={val => handleChange("phone", val)}/>
        <BusinessAddressField value={values.address} onChange={val => handleChange("address", val)}/>
        <CreateBusinessButton onClick={handleSubmit} isLoading={isPending || isUploading} disabled={!isValid || isUploading}/>
      </Stack>
    </Paper>
  );
};