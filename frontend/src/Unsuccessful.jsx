import * as React from "react";
import { CssVarsProvider } from "@mui/joy/styles";
import CssBaseline from "@mui/joy/CssBaseline";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import Breadcrumbs from "@mui/joy/Breadcrumbs";
import Link from "@mui/joy/Link";
import Typography from "@mui/joy/Typography";
import axios from "axios";

import HomeRoundedIcon from "@mui/icons-material/HomeRounded";
import ChevronRightRoundedIcon from "@mui/icons-material/ChevronRightRounded";

// import Sidebar from "./components/Sidebar";
import OrderTable from "./components/Unsuccessful";
// import OrderList from "./components/OrderList";
// import Header from "./components/Header";

export default function JoyOrderDashboardTemplate() {
  const handleRetry = async () => {
    try {
      const response = await axios.post("http://127.0.0.1:5500/retry");
      if (response.status === 200) {
        alert("Retry process completed successfully.");
      } else {
        alert("Retry process failed.");
      }
    } catch (error) {
      console.error("Error retrying calls:", error);
      alert("An error occurred while retrying the calls.");
    }
  };

  return (
    <CssVarsProvider disableTransitionOnChange>
      <CssBaseline />
      <Box sx={{ display: "flex", minHeight: "100dvh" }}>
        {/* <Header /> */}
        {/* <Sidebar /> */}
        <Box
          component="main"
          className="MainContent"
          sx={{
            px: { xs: 2, md: 6 },
            pt: {
              xs: "calc(12px + var(--Header-height))",
              sm: "calc(12px + var(--Header-height))",
              md: 3,
            },
            pb: { xs: 2, sm: 2, md: 3 },
            flex: 1,
            display: "flex",
            flexDirection: "column",
            minWidth: 0,
            height: "100dvh",
            gap: 1,
          }}
        >
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <Breadcrumbs
              size="sm"
              aria-label="breadcrumbs"
              separator={<ChevronRightRoundedIcon fontSize="sm" />}
              sx={{ pl: 0 }}
            >
              <Link underline="none" color="neutral" href="/" aria-label="Home">
                <HomeRoundedIcon />
              </Link>
              <Link
                underline="none"
                color="neutral"
                href="/order"
                aria-label="Home"
              >
                All calls
              </Link>

              <Typography color="primary" fontWeight={500} fontSize={12}>
                Unsuccessful calls
              </Typography>
            </Breadcrumbs>
          </Box>
          <Box
            sx={{
              display: "flex",
              mb: 1,
              gap: 1,
              flexDirection: { xs: "column", sm: "row" },
              alignItems: { xs: "start", sm: "center" },
              flexWrap: "wrap",
              justifyContent: "space-between",
            }}
          >
            <Typography level="h2" component="h1">
              Orders
            </Typography>
            <Button color="danger" size="sm" onClick={handleRetry}>
              Retry
            </Button>
          </Box>
          <OrderTable />
          {/* <OrderList /> */}
        </Box>
      </Box>
    </CssVarsProvider>
  );
}
