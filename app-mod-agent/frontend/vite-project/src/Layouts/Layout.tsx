import React, { useState, useContext } from "react";
import { useTheme } from "@mui/material/styles";
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CssBaseline,
  Box,
  IconButton,
  Button,
  ListSubheader,
  Divider,
  AppBar as MuiAppBar,
  Toolbar,
  Stack,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { Link, Outlet, useNavigate, useLocation } from "react-router-dom";

import { ColorModeContext } from "../App";
import { ChatInputFooter } from "../components/ChatInputFooter";
import logo from "../assets/spark-final.png";
import { useChatContext } from "../contexts/ChatContext";

import MenuIcon from "@mui/icons-material/Menu";
import ChevronLeftIcon from "@mui/icons-material/ChevronLeft";
import AddIcon from "@mui/icons-material/Add";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import AutoAwesomeIcon from "@mui/icons-material/AutoAwesome";
import LightbulbOutlinedIcon from "@mui/icons-material/LightbulbOutlined";
import BugReportOutlinedIcon from "@mui/icons-material/BugReportOutlined";
import Brightness4Icon from "@mui/icons-material/Brightness4";
import Brightness7Icon from "@mui/icons-material/Brightness7";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";

const drawerWidth = 260;

const Main = styled("main", { shouldForwardProp: (prop) => prop !== "open" })<{
  open?: boolean;
}>(({ theme, open }) => ({
  flexGrow: 1,
  padding: 0,
  transition: theme.transitions.create("margin", {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  marginLeft: `-${drawerWidth}px`,
  display: "flex",
  flexDirection: "column",
  height: "100vh",
  ...(open && {
    transition: theme.transitions.create("margin", {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
    marginLeft: 0,
  }),
}));

const AppBar = styled(MuiAppBar, {
  shouldForwardProp: (prop) => prop !== "open",
})<{ open?: boolean }>(({ theme, open }) => ({
  transition: theme.transitions.create(["margin", "width"], {
    easing: theme.transitions.easing.sharp,
    duration: theme.transitions.duration.leavingScreen,
  }),
  ...(open && {
    width: `calc(100% - ${drawerWidth}px)`,
    marginLeft: `${drawerWidth}px`,
    transition: theme.transitions.create(["margin", "width"], {
      easing: theme.transitions.easing.easeOut,
      duration: theme.transitions.duration.enteringScreen,
    }),
  }),
}));

const DrawerHeader = styled("div")(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  padding: theme.spacing(0, 1),
  ...theme.mixins.toolbar,
  justifyContent: "space-between",
}));

const agentList = [{ name: "SPARC", icon: <AutoAwesomeIcon /> }];

const Layout: React.FC = () => {
  const [open, setOpen] = useState(true);
  const navigate = useNavigate(); 
  const location = useLocation();
  const theme = useTheme();
  const colorMode = useContext(ColorModeContext);

  // Get everything needed from the chat context
  const {
    messages,
    isLoading,
    handleSubmit: originalHandleSubmit,
    clearChat,
  } = useChatContext();

  const handleDrawerOpen = () => setOpen(true);
  const handleDrawerClose = () => setOpen(false);

  const handleClearChat = () => {
    clearChat();
    navigate("/");
  };

  const handleStartNewChat = () => {
    clearChat();
    navigate("/");
  };

  const handleSubmitAndNavigate = (query: string, files: File[]) => {

    originalHandleSubmit(query, files);

    if (location.pathname === "/") {
      navigate("/chat");
    }
  };

  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        open={open}
        sx={{
          background: "rgba(255, 255, 255, 0.1)",
          backdropFilter: "blur(10px)",
          WebkitBackdropFilter: "blur(10px)",
          color: theme.palette.mode === "dark" ? "#fff" : "#111",
          boxShadow: "0 2px 10px rgba(0,0,0,0.1)",
          borderBottom: "1px solid rgba(255,255,255,0.2)",
        }}
      >
        <Toolbar sx={{ justifyContent: "space-between" }}>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            onClick={handleDrawerOpen}
            edge="start"
            sx={{ mr: 2, ...(open && { display: "none" }) }}
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Drawer
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          "& .MuiDrawer-paper": {
            width: drawerWidth,
            boxSizing: "border-box",
            borderRight: "none", 
            boxShadow: theme.shadows[3],
          },
        }}
        variant="persistent"
        anchor="left"
        open={open}
      >
        <DrawerHeader>
          <Link to="/" style={{ textDecoration: "none", color: "inherit" }}>
            <Box
              component="img"
              src={logo}
              alt="SPARC logo"
              sx={{ height: 40, pl: 1 }}
            />
          </Link>
          <IconButton onClick={handleDrawerClose}>
            <ChevronLeftIcon />
          </IconButton>
        </DrawerHeader>

        <Box sx={{ px: 2, mb: 2 }}>
          <Stack spacing={1}>
            <Button
              onClick={handleStartNewChat}
              variant="outlined"
              startIcon={<AddIcon />}
              fullWidth
              sx={{
                justifyContent: "flex-start",
                textTransform: "none",
                position: "relative", 
                overflow: "hidden", 
                transition: "color 0.3s ease-in-out",
                zIndex: 1, 

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
                  zIndex: -1, 
                },

                // Default state styling
                ...(theme.palette.mode === "dark"
                  ? {
                      borderColor: "#FFEB3B",
                      color: "#FFEB3B",
                    }
                  : {
                      borderColor: "grey.500",
                      color: "text.primary",
                    }),

                "&:hover": {
                  color: "#000000", 
                  borderColor: "transparent", 
                  "&::before": {
                    opacity: 1, 
                  },
                  "& .MuiSvgIcon-root": {
                    color: "#000000",
                  },
                },
              }}
            >
              Start new chat
            </Button>
            {messages.length > 0 && (
              <Button
                onClick={handleClearChat}
                variant="outlined"
                color="error"
                startIcon={<DeleteOutlineIcon />}
                fullWidth
                sx={{ justifyContent: "flex-start", textTransform: "none" }}
              >
                Clear Chat
              </Button>
            )}
          </Stack>
        </Box>

        <List
          subheader={
            <ListSubheader
              sx={{
                bgcolor: "transparent",
                fontWeight: "bold",
                color: theme.palette.mode === "dark" ? "#FFEB3B" : "#E65100",
              }}
            >
              Agents
            </ListSubheader>
          }
        >
          {agentList.map((agent) => (
            <ListItemButton
              key={agent.name}
              selected={agent.name === "SPARC"}
              sx={{
                "&.Mui-selected":
                  theme.palette.mode === "dark"
                    ? {
                        backgroundColor: "rgba(255, 235, 59, 0.16)",
                        "& .MuiListItemIcon-root, & .MuiListItemText-primary": {
                          color: "#FFEB3B",
                        },
                        "&:hover": {
                          backgroundColor: "rgba(255, 235, 59, 0.2)",
                        },
                      }
                    : {
                        backgroundColor: "rgba(255, 152, 0, 0.1)",
                        "& .MuiListItemIcon-root, & .MuiListItemText-primary": {
                          color: "#E65100",
                        },
                        "&:hover": {
                          backgroundColor: "rgba(255, 152, 0, 0.15)",
                        },
                      },
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>{agent.icon}</ListItemIcon>
              <ListItemText primary={agent.name} />
            </ListItemButton>
          ))}
        </List>

        <Box sx={{ flexGrow: 1 }} />
        <Divider />
        <List>
          <ListItem>
            <ListItemText primary="Theme" />
            <IconButton
              sx={{ ml: 1 }}
              onClick={colorMode.toggleColorMode}
              color="inherit"
            >
              {theme.palette.mode === "dark" ? (
                <Brightness7Icon />
              ) : (
                <Brightness4Icon />
              )}
            </IconButton>
          </ListItem>
          {/* ▼▼▼ 2. ADD THIS NEW LIST ITEM BUTTON ▼▼▼ */}
          <ListItemButton component={Link} to="/about">
            <ListItemIcon>
              <InfoOutlinedIcon />
            </ListItemIcon>
            <ListItemText primary="About" />
          </ListItemButton>
          <ListItemButton>
            <ListItemIcon>
              <LightbulbOutlinedIcon />
            </ListItemIcon>
            <ListItemText primary="Feature Request" />
          </ListItemButton>
          <ListItemButton>
            <ListItemIcon>
              <BugReportOutlinedIcon />
            </ListItemIcon>
            <ListItemText primary="Bug Report" />
          </ListItemButton>
        </List>
      </Drawer>

      <Main open={open}>
        <DrawerHeader />
        <Box sx={{ flexGrow: 1, overflow: "auto", p: 3 }}>
          <Outlet />
        </Box>
        <Box
          component="footer"
          sx={{
            display: "flex",
            justifyContent: "center",
            p: 2,
            width: "100%",
          }}
        >
          <ChatInputFooter
            handleSubmit={handleSubmitAndNavigate}
            isLoading={isLoading}
          />
        </Box>
      </Main>
    </Box>
  );
};

export default Layout;
