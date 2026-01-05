import {
  Box,
  Typography,
  Grid,
  Paper,
  useTheme,
} from "@mui/material";
import logo from "../assets/spark-final.png";
import { motion } from "framer-motion";
import { useChatContext } from "../contexts/ChatContext";
import { useNavigate } from "react-router-dom";

const suggestionPrompts = [
  "Generate a conceptual architecture for a new mobile banking app.",
  "Recommend a cloud migration strategy for a legacy Java monolith.",
  "Analyze our application portfolio and identify the best candidates for modernization.",
  "Create a sample Statement of Work (SOW) for a 3-month Apigee implementation.",
  "Generate unit tests for this Spring Boot controller I've uploaded.",
  "Scaffold a new microservice using Python and Flask with a CI/CD pipeline.",
  "Draft a migration roadmap for containerizing on-prem applications using Kubernetes.",
  "Summarize the pros and cons of using serverless architecture for enterprise workloads.",
];

export function WelcomeScreen() {
  const { handleSubmit, isLoading } = useChatContext();
  const navigate = useNavigate();

  const handleSuggestionClick = (prompt: string) => {
    if (!isLoading) {
      handleSubmit(prompt, []);
      navigate("/chat");
    }
  };
  const theme = useTheme();

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        height: "100%",
        textAlign: "center",
        p: 2,
      }}
    >
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Box sx={{ mb: 4 }}>
          <Box
            component="img"
            src={logo}
            alt="SPARC Logo"
            sx={{
              height: 120,
              mb: 3,
              filter: "drop-shadow(0px 10px 25px rgba(0, 0, 0, 0.2))",
            }}
          />
          <Typography
            variant="h3"
            component="h1"
            sx={{
              fontWeight: "bold",
              mb: 1,
              background: "linear-gradient(45deg, #FFEB3B, #F57C00, #FF9800)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
            }}
          >
            SPARC
          </Typography>
          <Typography variant="h6" color="text.secondary">
            Strategic Platform for Application Re-architecting & Conversion
          </Typography>
        </Box>
      </motion.div>

      <Grid
        container
        spacing={2}
        sx={{
          maxWidth: "1100px",
          justifyContent: "center",
          display: "flex",
          flexWrap: "wrap",
        }}
      >
        {suggestionPrompts.map((prompt, index) => (
          <Grid
            item
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            {...({ xs: 12, sm: 6, md: 3 } as any)}
            key={prompt}
            sx={{
              width: {
                xs: "100%",
                sm: "48%",
                md: "23%",
              },
              display: "flex",
              justifyContent: "center",
            }}
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.2 + index * 0.05 }}
              style={{ width: "100%", height: "100%" }}
            >
              <Paper
                variant="outlined"
                onClick={() => handleSuggestionClick(prompt)}
                sx={{
                  p: 2,
                  width: "100%",
                  height: "100%",
                  cursor: "pointer",
                  minHeight: "140px",
                  borderRadius: "16px",
                  textAlign: "center",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  position: "relative",
                  overflow: "hidden",
                  backgroundColor:
                    theme.palette.mode === "light"
                      ? theme.palette.grey[50]
                      : theme.palette.action.hover,
                  borderColor: theme.palette.divider,
                  transition: "transform 0.3s ease, box-shadow 0.3s ease",
                  "&::before": {
                    content: '""',
                    position: "absolute",
                    top: 0,
                    left: 0,
                    width: "100%",
                    height: "100%",
                    backgroundImage: "linear-gradient(45deg, #FFD600, #FF9100)",
                    opacity: 0,
                    transition: "opacity 0.3s ease-in-out",
                    zIndex: 0,
                  },
                  "& .MuiTypography-root": {
                    position: "relative",
                    zIndex: 1,
                    transition: "color 0.3s ease-in-out",
                  },
                  "&:hover": {
                    borderColor: "transparent",
                    transform: "translateY(-5px)",
                    boxShadow: "0 10px 20px rgba(255, 165, 0, 0.25)",
                    "&::before": {
                      opacity: 1,
                    },
                    "& .MuiTypography-root": {
                      color: "#000000",
                    },
                  },
                }}
              >
                <Typography variant="body2" color="text.secondary">
                  {prompt}
                </Typography>
              </Paper>
            </motion.div>
          </Grid>
        ))}
      </Grid>

      <Box sx={{ flexGrow: 1 }} />
    </Box>
  );
}
