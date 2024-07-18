/* eslint-disable jsx-a11y/anchor-is-valid */
import * as React from "react";
import axios from "axios";
import { ColorPaletteProp } from "@mui/joy/styles";
import Avatar from "@mui/joy/Avatar";
import Box from "@mui/joy/Box";
import Button from "@mui/joy/Button";
import Chip from "@mui/joy/Chip";
import Divider from "@mui/joy/Divider";
import FormControl from "@mui/joy/FormControl";
import FormLabel from "@mui/joy/FormLabel";
import Link from "@mui/joy/Link";
import Input from "@mui/joy/Input";
import Modal from "@mui/joy/Modal";
import ModalDialog from "@mui/joy/ModalDialog";
import ModalClose from "@mui/joy/ModalClose";
import Select from "@mui/joy/Select";
import Option from "@mui/joy/Option";
import Table from "@mui/joy/Table";
import Sheet from "@mui/joy/Sheet";
import Checkbox from "@mui/joy/Checkbox";
import IconButton, { iconButtonClasses } from "@mui/joy/IconButton";
import Typography from "@mui/joy/Typography";
import Menu from "@mui/joy/Menu";
import MenuButton from "@mui/joy/MenuButton";
import MenuItem from "@mui/joy/MenuItem";
import Dropdown from "@mui/joy/Dropdown";

import FilterAltIcon from "@mui/icons-material/FilterAlt";
import SearchIcon from "@mui/icons-material/Search";
import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import CheckRoundedIcon from "@mui/icons-material/CheckRounded";
import BlockIcon from "@mui/icons-material/Block";
import AutorenewRoundedIcon from "@mui/icons-material/AutorenewRounded";
import KeyboardArrowRightIcon from "@mui/icons-material/KeyboardArrowRight";
import KeyboardArrowLeftIcon from "@mui/icons-material/KeyboardArrowLeft";
import MoreHorizRoundedIcon from "@mui/icons-material/MoreHorizRounded";
const fetchData = async (setRows) => {
  try {
    const response = await axios.get(
      `https://trading-call.onrender.com/unsuccessful`
    );
    const data = response.data.clients.map((client) => ({
      client_id: client.client_id,
      client_name: client.client_name,
      phone_number: client.phone_number,
    }));
    setRows(data);
  } catch (error) {
    console.error("Error fetching data", error);
  }
};

function descendingComparator(a, b, orderBy) {
  if (b[orderBy] < a[orderBy]) {
    return -1;
  }
  if (b[orderBy] > a[orderBy]) {
    return 1;
  }
  return 0;
}

function getComparator(order, orderBy) {
  return order === "desc"
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy);
}

function stableSort(array, comparator) {
  const stabilizedThis = array.map((el, index) => [el, index]);
  stabilizedThis.sort((a, b) => {
    const order = comparator(a[0], b[0]);
    if (order !== 0) {
      return order;
    }
    return a[1] - b[1];
  });
  return stabilizedThis.map((el) => el[0]);
}

export default function OrderTable() {
  const [order, setOrder] = React.useState("desc");
  const [selected, setSelected] = React.useState([]);
  const [rows, setRows] = React.useState([]);

  React.useEffect(() => {
    fetchData(setRows);
  }, []);

  return (
    <React.Fragment>
      <Sheet
        className="OrderTableContainer"
        variant="outlined"
        sx={{
          display: { xs: "none", sm: "initial" },
          width: "100%",
          borderRadius: "sm",
          flexShrink: 1,
          overflow: "auto",
          minHeight: 0,
        }}
      >
        <Table
          aria-labelledby="tableTitle"
          stickyHeader
          hoverRow
          sx={{
            "--TableCell-headBackground":
              "var(--joy-palette-background-level1)",
            "--Table-headerUnderlineThickness": "1px",
            "--TableRow-hoverBackground":
              "var(--joy-palette-background-level1)",
            "--TableCell-paddingY": "4px",
            "--TableCell-paddingX": "8px",
          }}
        >
          <thead>
            <tr>
              <th
                style={{ width: 48, textAlign: "center", padding: "12px 6px" }}
              >
                <Checkbox
                  size="sm"
                  indeterminate={
                    selected.length > 0 && selected.length !== rows.length
                  }
                  checked={selected.length === rows.length}
                  onChange={(event) => {
                    setSelected(
                      event.target.checked
                        ? rows.map((row) => row.client_id)
                        : []
                    );
                  }}
                  color={
                    selected.length > 0 || selected.length === rows.length
                      ? "primary"
                      : undefined
                  }
                  sx={{ verticalAlign: "text-bottom" }}
                />
              </th>
              <th style={{ width: 120, padding: "12px 6px" }}>
                <Link
                  underline="none"
                  color="primary"
                  component="button"
                  onClick={() => setOrder(order === "asc" ? "desc" : "asc")}
                  fontWeight="lg"
                  endDecorator={<ArrowDropDownIcon />}
                  sx={{
                    "& svg": {
                      transition: "0.2s",
                      transform:
                        order === "asc" ? "rotate(0deg)" : "rotate(180deg)",
                    },
                  }}
                >
                  Client ID
                </Link>
              </th>
              <th style={{ width: 120, padding: "12px 6px" }}>Client Name</th>
              <th style={{ width: 120, padding: "12px 6px" }}>Phone Number</th>
            </tr>
          </thead>
          <tbody>
            {stableSort(rows, getComparator(order, "client_id")).map((row) => (
              <tr key={row.client_id}>
                <td style={{ textAlign: "center" }}>
                  <Checkbox
                    size="sm"
                    checked={selected.includes(row.client_id)}
                    onChange={(event) => {
                      setSelected((ids) =>
                        event.target.checked
                          ? [...ids, row.client_id]
                          : ids.filter((item) => item !== row.client_id)
                      );
                    }}
                    sx={{ verticalAlign: "text-bottom" }}
                    color={
                      selected.includes(row.client_id) ? "primary" : undefined
                    }
                  />
                </td>
                <td>{row.client_id}</td>
                <td>{row.client_name}</td>
                <td>{row.phone_number}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Sheet>
      <Box
        className="Pagination-mobile"
        sx={{
          display: { xs: "flex", sm: "none" },
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <IconButton size="sm" color="neutral" variant="outlined">
          <KeyboardArrowLeftIcon />
        </IconButton>
        <Typography level="body2" textAlign="center" sx={{ flex: 1 }}>
          1-5 of 30
        </Typography>
        <IconButton size="sm" color="neutral" variant="outlined">
          <KeyboardArrowRightIcon />
        </IconButton>
      </Box>
      <Box
        className="Pagination-tabletUp"
        sx={{
          borderTop: "1px solid",
          borderColor: "divider",
          bgcolor: "background.level1",
          py: 2,
          px: 2,
          display: { xs: "none", sm: "flex" },
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <Box sx={{ display: "flex", gap: 1.5 }}>
          <Typography level="body2" sx={{ alignSelf: "center" }}>
            1-5 of 30
          </Typography>
        </Box>
        <Box sx={{ display: "flex", gap: 1.5 }}>
          <IconButton size="sm" color="neutral" variant="outlined">
            <KeyboardArrowLeftIcon />
          </IconButton>
          <IconButton size="sm" color="neutral" variant="outlined">
            <KeyboardArrowRightIcon />
          </IconButton>
        </Box>
      </Box>
    </React.Fragment>
  );
}
