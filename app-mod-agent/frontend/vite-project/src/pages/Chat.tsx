import React from "react";
import { ChatMessagesView } from "../components/ChatMessagesView";
import { useChatContext } from "../contexts/ChatContext";

const Chat: React.FC = () => {
  const { messages, isLoading } = useChatContext();

  return <ChatMessagesView messages={messages} isLoading={isLoading} />;
};

export default Chat;
