import { Box, Typography, Button, Paper } from "@mui/material";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";

export const BackendUnavailable = () => (
  <Box
    sx={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      height: "100vh",
      backgroundColor: "#f5f5f5",
    }}
  >
    <Paper
      elevation={3}
      sx={{ p: 4, textAlign: "center", borderRadius: "16px" }}
    >
      <ErrorOutlineIcon color="error" sx={{ fontSize: 60, mb: 2 }} />
      <Typography variant="h5" component="h2" gutterBottom>
        Backend Unavailable
      </Typography>
      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Unable to connect to backend services.
      </Typography>
      <Button variant="contained" onClick={() => window.location.reload()}>
        Retry
      </Button>
    </Paper>
  </Box>
);
