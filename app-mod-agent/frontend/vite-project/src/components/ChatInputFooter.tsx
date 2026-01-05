import React from "react";
import { Box, Typography, Stack } from "@mui/material";
import { InputForm } from "./InputForm";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";

interface ChatInputFooterProps {
  handleSubmit: (query: string, files: File[]) => void;
  isLoading: boolean;
}

export const ChatInputFooter: React.FC<ChatInputFooterProps> = ({
  handleSubmit,
  isLoading,
}) => {
  return (
    <Box
      sx={{
        width: "100%",
        maxWidth: "md",
        mx: "auto",
        textAlign: "center",
      }}
    >
      <InputForm onSubmit={handleSubmit} isLoading={isLoading} context="chat" />
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ mt: 1.5, display: "block" }}
      >
        Generative AI may display inaccurate information, so double-check its
        responses.
      </Typography>

      <Stack
        direction="row"
        spacing={0.5}
        alignItems="center"
        justifyContent="center"
        sx={{ mt: 0.5 }}
      >
        <AutoAwesomeIcon sx={{ fontSize: "0.875rem", color: "#F57C00" }} />
        <Typography
          variant="caption"
          sx={{
            fontWeight: "medium",
            background: "linear-gradient(45deg, #FFEB3B, #F57C00)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          Powered by Gemini
        </Typography>
      </Stack>
    </Box>
  );
};
