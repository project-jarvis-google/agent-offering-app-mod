import React, { useRef, useEffect, useState } from "react";
import {
  Box,
  Paper,
  Stack,
  Avatar,
  Typography,
  Chip,
  IconButton,
  Tooltip,
  useTheme,
} from "@mui/material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import InsertDriveFileOutlinedIcon from "@mui/icons-material/InsertDriveFileOutlined";
import logo from "../assets/spark-final.png";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import CheckIcon from "@mui/icons-material/Check";
import GeminiLoader from "./GeminiLoader";

interface DisplayFile {
  name: string;
  type: string;
  url: string;
}

export interface Message {
  type: "human" | "ai";
  content: string;
  id: string;
  files?: DisplayFile[];
}

interface ChatMessagesViewProps {
  messages: Message[];
  isLoading: boolean;
}

const cleanContent = (text: string): string => {
    const jsonCodeBlockRegex = /```(json|code|bash|text)\s*\{[\s\S]*?\n\}\s*```/g;
    
    const cleanedText = text.replace(jsonCodeBlockRegex, '').trim();
    
    if (cleanedText === "" || (cleanedText.startsWith('{') && cleanedText.endsWith('}'))) {
        return "The system processed the request and generated the final report below.";
    }
    
    return cleanedText;
};


const AIMessageBubble: React.FC<{ message: Message }> = ({ message }) => {
  const [isCopied, setIsCopied] = useState(false);
  const theme = useTheme();

  const handleCopy = async () => {
    if (!message.content) return;
    try {
      await navigator.clipboard.writeText(message.content);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  return (
    <Stack
      key={message.id}
      direction="row"
      spacing={2}
      sx={{
        justifyContent: "flex-start",
        alignItems: "flex-start",
        maxWidth: "100%",
      }}
    >
      <Avatar
        src={logo}
        sx={{ width: 40, height: 40, bgcolor: "transparent" }}
      />
      <Box sx={{ maxWidth: "calc(100% - 56px)" }}>
        <Typography sx={{ fontWeight: "bold", mb: 0.5 }}>SPARC</Typography>
        <Paper
          elevation={0}
          sx={{
            p: 1.5,
            bgcolor: theme.palette.action.hover,
            color: theme.palette.text.primary,
            borderRadius: "20px 20px 20px 4px",
            "&:hover .copy-button": {
              opacity: 1,
            },
          }}
        >
          <Stack direction="row" spacing={1} alignItems="flex-start">
            <Typography
              component="div"
              sx={{
                "& p": { margin: 0 },
                wordBreak: "break-word",
                flexGrow: 1,
              }}
            >
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code(props) {
                    const { children, className } = props;
                    const match = /language-(\w+)/.exec(className || "");
                    return match ? (
                      <SyntaxHighlighter
                        PreTag="div"
                        language={match[1]}
                        style={vscDarkPlus}
                      >
                        {String(children).replace(/\n$/, "")}
                      </SyntaxHighlighter>
                    ) : (
                      <code
                        className={className}
                        {...props}
                        style={{
                          backgroundColor: "rgba(255, 255, 255, 0.1)",
                          padding: "2px 4px",
                          borderRadius: "4px",
                        }}
                      >
                        {children}
                      </code>
                    );
                  },
                  a: ({ ...props }) => (
                    <a 
                        {...props} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        style={{ 
                            color: theme.palette.primary.light, 
                            textDecoration: 'underline',
                            fontWeight: 'bold'
                        }}
                    >
                        {props.children}
                    </a>
                  )
                }}
              >
                {cleanContent(message.content)}
              </ReactMarkdown>
            </Typography>

            <Tooltip title={isCopied ? "Copied!" : "Copy"} placement="top">
              <IconButton
                onClick={handleCopy}
                className="copy-button"
                sx={{
                  opacity: 0,
                  transition: "opacity 0.2s",
                  alignSelf: "flex-end",
                }}
              >
                {isCopied ? (
                  <CheckIcon fontSize="small" />
                ) : (
                  <ContentCopyIcon fontSize="small" />
                )}
              </IconButton>
            </Tooltip>
          </Stack>
        </Paper>
      </Box>
    </Stack>
  );
};

export function ChatMessagesView({
  messages,
  isLoading,
}: ChatMessagesViewProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const theme = useTheme();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages, isLoading]);

  return (
    <Box
      sx={{
        flexGrow: 1,
        display: "flex",
        flexDirection: "column",
        overflow: "hidden",
      }}
    >
      <Box sx={{ flexGrow: 1, overflowY: "auto", p: { xs: 1, sm: 2, md: 3 } }}>
        <Stack spacing={3} sx={{ maxWidth: "md", mx: "auto" }}>
          {messages.map((message) => {
            if (message.type === "ai") {
              return message.content || (message.files && message.files.length > 0) ? (
                <AIMessageBubble key={message.id} message={message} />
              ) : null;
            }
            return (
              <Stack
                key={message.id}
                direction="row"
                spacing={2}
                sx={{ justifyContent: "flex-end", alignItems: "flex-start" }}
              >
                <Box sx={{ maxWidth: "80%" }}>
                  <Typography
                    sx={{ fontWeight: "bold", mb: 0.5, textAlign: "right" }}
                  >
                    You
                  </Typography>
                  <Paper
                    elevation={0}
                    sx={{
                      p: 1.5,
                      backgroundImage:
                        "linear-gradient(90deg, #FFEB3B, #F57C00)",
                      color: "#000000",
                      borderRadius: "20px 20px 4px 20px",
                    }}
                  >
                    {message.files && message.files.length > 0 && (
                      <Stack spacing={1} sx={{ mb: message.content ? 1.5 : 0 }}>
                        {message.files.map((file, index) => (
                          <Paper
                            key={index}
                            variant="outlined"
                            sx={{
                              p: 1,
                              borderRadius: "12px",
                              bgcolor: "background.default",
                            }}
                          >
                            {file.type.startsWith("image/") ? (
                              <Box
                                component="img"
                                src={file.url}
                                alt={file.name}
                                sx={{
                                  maxWidth: "100%",
                                  maxHeight: "200px",
                                  borderRadius: "8px",
                                  objectFit: "contain",
                                }}
                              />
                            ) : (
                              <Chip
                                icon={<InsertDriveFileOutlinedIcon />}
                                label={file.name}
                                variant="outlined"
                                sx={{
                                  height: "auto",
                                  "& .MuiChip-label": { p: 1 },
                                }}
                              />
                            )}
                          </Paper>
                        ))}
                      </Stack>
                    )}
                    {message.content && (
                      <Typography
                        component="div"
                        sx={{ "& p": { margin: 0 }, wordBreak: "break-word" }}
                      >
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {message.content}
                        </ReactMarkdown>
                      </Typography>
                    )}
                  </Paper>
                </Box>
                <Avatar
                  sx={{
                    bgcolor: theme.palette.grey[400],
                    width: 40,
                    height: 40,
                  }}
                >
                  <PersonOutlineOutlinedIcon />
                </Avatar>
              </Stack>
            );
          })}
          {isLoading && (
            <Stack
              direction="row"
              spacing={2}
              sx={{ justifyContent: "flex-start", alignItems: "center" }}
            >
              <Avatar
                src={logo}
                sx={{ width: 40, height: 40, bgcolor: "transparent" }}
              />

              <GeminiLoader />
            </Stack>
          )}
          <div ref={scrollRef} />
        </Stack>
      </Box>
    </Box>
  );
}
