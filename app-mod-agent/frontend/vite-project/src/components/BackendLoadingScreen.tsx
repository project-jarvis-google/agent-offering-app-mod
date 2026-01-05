import { Box, Typography } from "@mui/material";
import { keyframes } from "@mui/system";
import logo from "../assets/spark-final.png";

const pulseAnimation = keyframes`
  0% { transform: scaleY(0.5); opacity: 0.7; }
  50% { transform: scaleY(1); opacity: 1; }
  100% { transform: scaleY(0.5); opacity: 0.7; }
`;

export const BackendLoadingScreen = () => (
  <Box
    sx={{
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      justifyContent: "center",
      height: "100vh",
      width: "100vw",
      backgroundColor: "background.default",
    }}
  >
    <Box
      component="img"
      src={logo}
      alt="SPARC Logo"
      sx={{ height: 80, mb: 3 }}
    />
    <Typography variant="h4" component="h1" sx={{ fontWeight: "bold", mb: 1 }}>
      SPARC
    </Typography>
    <Typography variant="h6" color="text.secondary" sx={{ mb: 4 }}>
      Waiting for backend to be ready...
    </Typography>

    <Box
      sx={{
        height: "6px",
        width: "120px",
        backgroundColor: "text.secondary",
        borderRadius: "3px",
        animation: `${pulseAnimation} 1.5s ease-in-out infinite`,
      }}
    />
  </Box>
);
