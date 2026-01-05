import { useState, useCallback, useRef } from "react";

export interface DisplayFile {
  name: string;
  type: string;
  url: string;
}

export interface MessageWithAgent {
  type: "human" | "ai";
  content: string;
  id: string;
  agent?: string;
  finalReportWithCitations?: boolean;
  files?: DisplayFile[];
}

export interface ProcessedEvent {
  title: string;
  data: unknown;
}

interface AgentPart {
  text?: string;
  inlineData?: {
    displayName: string;
    data: string;
    mimeType: string;
  };
  fileData?: {
    displayName?: string;
    fileUri: string;
    mimeType: string;
  };
}

interface AgentResponseChunk {
  error?: string | { message?: string; code?: number };
  content?: {
    parts?: AgentPart[];
  };
  author?: string;
  partial?: boolean;
}

const createLocalPreview = (file: File) =>
  new Promise<DisplayFile>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      resolve({
        name: file.name,
        type: file.type,
        url: reader.result as string,
      });
    };
    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });

const base64ToBlobUrl = (base64Data: string, mimeType: string) => {
  const base64Content = base64Data.split(",")[1] || base64Data;
  const byteCharacters = atob(base64Content);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  const blob = new Blob([byteArray], { type: mimeType });
  return URL.createObjectURL(blob);
};

const generateId = () => Math.random().toString(36).substring(2, 9);

export function useChat(apiBaseUrl: string) {
  const [userId, setUserId] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [appName, setAppName] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageWithAgent[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const abortControllerRef = useRef<AbortController | null>(null);
  const isSubmittingRef = useRef(false); 
  const hasContentBeenStreamedRef = useRef(false);

  const createSession = async () => {
    const response = await fetch(
      apiBaseUrl + `/apps/app/users/u_999/sessions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }
    );
    if (!response.ok)
      throw new Error(`Failed to create session. Status: ${response.status}`);
    return response.json();
  };

  const handleSubmit = useCallback(
    async (query: string, files: File[]) => {
      if ((!query.trim() && files.length === 0) || isLoading) return;
      if (isSubmittingRef.current) return;
      isSubmittingRef.current = true;
      setIsLoading(true);

      hasContentBeenStreamedRef.current = false;

      const aiMessageId = generateId() + "_ai";
      const userMessageId = generateId();

      try {
        let currentSessionId = sessionId;
        let currentUserId = userId;
        let currentAppName = appName;

        if (!currentSessionId || !currentUserId || !currentAppName) {
          const sessionData = await createSession();
          setUserId(sessionData.userId);
          setSessionId(sessionData.id);
          setAppName(sessionData.appName);
          currentSessionId = sessionData.id;
          currentUserId = sessionData.userId;
          currentAppName = sessionData.appName;
        }

        const displayFiles = await Promise.all(files.map(createLocalPreview));

        const filePartPromises = files.map(async (file) => {
          try {
            const isTextFile = file.type === "text/csv" || file.type === "text/plain";
            const reader = new FileReader();
            
            const dataPromise = new Promise<{
              name: string;
              type: string;
              data: string;
            }>((resolve, reject) => {
              reader.onload = () => {
                const result = reader.result as string;
                let base64Data: string;

                if (isTextFile) {
                  // For text files, the result is a plain string. Encode it to base64.
                  // This is the robust way to handle UTF-8 text encoding.
                  base64Data = btoa(unescape(encodeURIComponent(result)));
                } else {
                  // For binary files (PDF, image, etc.), result is a Data URL. Extract the base64 part.
                  if (result.includes(",")) {
                    const [, base64] = result.split(",");
                    base64Data = base64;
                  } else {
                    base64Data = result;
                  }
                }
                
                resolve({ name: file.name, type: file.type, data: base64Data });
              };
              reader.onerror = (err) => reject(err);

              if (isTextFile) {
                reader.readAsText(file);
              } else {
                reader.readAsDataURL(file);
              }
            });
            
            const fileData = await dataPromise;
            return {
              inlineData: {
                displayName: fileData.name,
                data: fileData.data,
                mimeType: fileData.type,
              },
            };
          } catch (err) {
            console.error(`Failed to read file ${file.name}:`, err);
            return null;
          }
        });

        const fileParts = await Promise.all(filePartPromises);
        const validFileParts = fileParts.filter(Boolean);

        setMessages((prev) => [
          ...prev,
          {
            type: "human",
            content: query,
            id: userMessageId,
            files: displayFiles,
          },
          { type: "ai", content: "", id: aiMessageId },
        ]);

        const messageParts: AgentPart[] = [];
        if (query.trim()) messageParts.push({ text: query });
        messageParts.push(...(validFileParts as AgentPart[]));

        const payload = {
          appName: currentAppName,
          userId: currentUserId,
          sessionId: currentSessionId,
          newMessage: { parts: messageParts, role: "user" },
          streaming: true,
        };

        abortControllerRef.current = new AbortController();
        const response = await fetch(apiBaseUrl + `/run_sse`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok || !response.body)
          throw new Error(`API call failed with status: ${response.status}`);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let done = false;
        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk
            .split("\n")
            .filter((line) => line.startsWith("data: "));

          for (const line of lines) {
            const jsonText = line.substring(5).trim();
            if (!jsonText) continue;
            try {
              const json = JSON.parse(jsonText) as AgentResponseChunk;

              if (json.error)
                throw new Error(
                  (json.error as { message?: string }).message ||
                    json.error.toString()
                );

              const textParts = json?.content?.parts
                ?.map((p: AgentPart) => p.text)
                .filter(Boolean)
                .join("");

              const shouldAppendText = !!textParts && json.partial === true;
              const hasNewContent =
                shouldAppendText ||
                (json?.content?.parts &&
                  json.content.parts.some((p) => p.fileData));

              if (hasNewContent) {
                hasContentBeenStreamedRef.current = true;

                setMessages((prev) =>
                  prev.map((m) => {
                    if (m.id === aiMessageId) {
                      const newContent =
                        m.content + (shouldAppendText ? textParts : "");
                      let newAgent = json.author || m.agent;
                      const newFiles = [...(m.files || [])];

                      if (json?.content?.parts) {
                        json.content.parts.forEach((p: AgentPart) => {
                          if (p.fileData) {
                            let fileUrl = p.fileData.fileUri;
                            if (fileUrl.startsWith("data:")) {
                              fileUrl = base64ToBlobUrl(
                                fileUrl,
                                p.fileData.mimeType
                              );
                            }
                            if (!newFiles.some((f) => f.url === fileUrl)) {
                              newFiles.push({
                                name:
                                  p.fileData.displayName || "Generated File",
                                type: p.fileData.mimeType,
                                url: fileUrl,
                              });
                            }
                          }
                        });
                      }

                      if (json.author) {
                        newAgent = json.author;
                      }

                      return {
                        ...m,
                        content: newContent,
                        agent: newAgent,
                        files: newFiles,
                      };
                    }
                    return m;
                  })
                );
              }
            } catch (e) {
              console.error("Could not parse chunk:", jsonText, e);
            }
          }
        }
        if (!hasContentBeenStreamedRef.current) {
          throw new Error("No valid content received from server.");
        }
      } catch (err: unknown) {
        console.error("Error during handleSubmit:", err);
        const errorMessage = err instanceof Error ? err.message : String(err);

        setMessages((prev) =>
          prev.map((m) =>
            m.id === aiMessageId 
              ? { ...m, content: `An error occurred: ${errorMessage}` }
              : m
          )
        );
      } finally {
        setIsLoading(false);
        isSubmittingRef.current = false;
      }
    },
    [isLoading, sessionId, userId, appName, apiBaseUrl, createSession]
  );

  const handleCancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setIsLoading(false);
      isSubmittingRef.current = false;
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setIsLoading(false);
    isSubmittingRef.current = false;
  }, []);

  return {
    messages,
    isLoading,
    handleSubmit, 
    handleCancel,
    clearChat,
  };
}
