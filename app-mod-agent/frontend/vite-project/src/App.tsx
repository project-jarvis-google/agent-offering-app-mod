import React, { useState, useMemo, createContext } from "react";
import { Routes, Route } from "react-router-dom";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";

import Home from "./pages/Home";
import Chat from "./pages/Chat";
import Layout from "./Layouts/Layout";
import { useBackendHealth } from "./hooks/useBackendHealth";
import { BackendLoadingScreen } from "./components/BackendLoadingScreen";
import { BackendUnavailable } from "./components/BackendUnavailable";
import { ChatProvider } from "./contexts/ChatContext";
import AboutPage from "./pages/About";

export const ColorModeContext = createContext({ toggleColorMode: () => {} });

const API_BASE_URL = "https://app-mod-agent-backend-428871167882.us-central1.run.app";

const App: React.FC = () => {
  const { isBackendReady, isCheckingBackend } = useBackendHealth(API_BASE_URL);

  const [mode, setMode] = useState<"light" | "dark">("light");

  const colorMode = useMemo(
    () => ({
      toggleColorMode: () => {
        setMode((prevMode) => (prevMode === "light" ? "dark" : "light"));
      },
    }),
    []
  );

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode,
          ...(mode === "light"
            ? {
                primary: { main: "#1976d2" },
                background: { default: "#ffffff", paper: "#ffffff" },
                text: { primary: "#000000", secondary: "#555555" },
              }
            : {
                primary: { main: "#BB86FC" },
                background: { default: "#121212", paper: "#1E1E1E" },
                text: { primary: "#FFFFFF", secondary: "#B3B3B3" },
                action: {
                  hover: "rgba(255, 255, 255, 0.08)",
                  selected: "rgba(255, 255, 255, 0.16)",
                },
              }),
        },
        typography: {
          fontFamily: "Roboto, Arial, sans-serif",
          h3: { fontWeight: 700 },
          h4: { fontWeight: 700 },
          h6: { fontWeight: 700 },
        },
      }),
    [mode]
  );

  if (isCheckingBackend) return <BackendLoadingScreen />;
  if (!isBackendReady) return <BackendUnavailable />;

  return (
    <ColorModeContext.Provider value={colorMode}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ChatProvider apiBaseUrl={API_BASE_URL}>
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<Home />} />
              <Route path="chat" element={<Chat />} />
              <Route path="about" element={<AboutPage />} />{" "}
            </Route>
          </Routes>
        </ChatProvider>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
};

export default App;
