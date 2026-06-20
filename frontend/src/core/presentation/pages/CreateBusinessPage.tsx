import { Container, Box } from "@mui/material";
import {CreateBusinessForm} from "../components/business/CreateBusinessForm.tsx";

export const CreateBusinessPage = () => {
  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          py: 4,
        }}
      >
        <CreateBusinessForm />
      </Box>
    </Container>
  );
};