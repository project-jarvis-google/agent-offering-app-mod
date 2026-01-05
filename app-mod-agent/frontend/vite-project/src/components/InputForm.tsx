import React, { useState, useRef } from "react";
import {
  Box,
  IconButton,
  Stack,
  Chip,
  OutlinedInput,
  InputAdornment,
} from "@mui/material";
import SendIcon from "@mui/icons-material/Send";
import AttachFileIcon from "@mui/icons-material/AttachFile";

interface InputFormProps {
  onSubmit: (query: string, files: File[]) => void;
  isLoading: boolean;
  context?: "homepage" | "chat";
}

export function InputForm({
  onSubmit,
  isLoading,
  context = "homepage",
}: InputFormProps) {
  const [inputValue, setInputValue] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const formRef = useRef<HTMLFormElement>(null); 

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (isLoading || (!inputValue.trim() && files.length === 0)) return;
    onSubmit(inputValue.trim(), files);
    setInputValue("");
    setFiles([]);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); 
      formRef.current?.requestSubmit();
    }
  };

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles((prev) => [...prev, ...Array.from(e.target.files!)]);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleRemoveFile = (indexToRemove: number) => {
    setFiles((prev) => prev.filter((_, index) => index !== indexToRemove));
  };

  const placeholderText =
    context === "chat" ? "Enter a prompt here" : "Ask me anything...";

  return (
    <Box>
      <input
        type="file"
        multiple
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: "none" }}
        accept="image/*,application/pdf,text/*,.csv,.doc,.docx,.xls,.xlsx"
      />

      <Box component="form" onSubmit={handleSubmit} ref={formRef}>
        {" "}
        {files.length > 0 && (
          <Stack
            direction="row"
            spacing={1}
            sx={{ mb: 1, flexWrap: "wrap", gap: 0.5 }}
          >
            {files.map((file, index) => (
              <Chip
                key={index}
                label={file.name}
                onDelete={() => handleRemoveFile(index)}
                size="small"
              />
            ))}
          </Stack>
        )}
        <OutlinedInput
          fullWidth
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholderText}
          multiline
          maxRows={5}
          sx={{
            borderRadius: "28px",
            backgroundColor: "action.hover",
            padding: "20px",
            "& .MuiOutlinedInput-notchedOutline": { border: "none" },
          }}
          startAdornment={
            <InputAdornment position="start">
              <IconButton
                onClick={handleUploadClick}
                disabled={isLoading}
                edge="start"
              >
                <AttachFileIcon />
              </IconButton>
            </InputAdornment>
          }
          endAdornment={
            <InputAdornment position="end">
              <IconButton
                type="submit"
                disabled={
                  isLoading || (!inputValue.trim() && files.length === 0)
                }
                edge="end"
                color="primary"
              >
                <SendIcon />
              </IconButton>
            </InputAdornment>
          }
        />
      </Box>
    </Box>
  );
}
