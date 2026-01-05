import React, { createContext, useContext, ReactNode } from "react";
import { useChat, MessageWithAgent } from "../hooks/useChat";

interface ChatContextType {
  messages: MessageWithAgent[];
  isLoading: boolean;
  handleSubmit: (query: string, files: File[]) => void;
  handleCancel: () => void;
  clearChat: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const ChatProvider: React.FC<{
  children: ReactNode;
  apiBaseUrl: string;
}> = ({ children, apiBaseUrl }) => {
  const chatLogic = useChat(apiBaseUrl);

  return (
    <ChatContext.Provider value={chatLogic}>{children}</ChatContext.Provider>
  );
};

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChatContext must be used within a ChatProvider");
  }
  return context;
};
