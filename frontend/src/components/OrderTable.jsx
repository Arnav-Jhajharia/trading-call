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

const fetchData = async (date, setRows) => {
  try {
    const response = await axios.get(
      `https://trading-call.onrender.com/calls?date=${date}`
    );
    const data = response.data.calls.map((call) => ({
      id: call[0],
      client_id: call[1],
      client_name: call[2],
      phone_number: call[3],
      date: call[4],
      download_status: call[7],
    }));
    setRows(data);
  } catch (error) {
    console.error("Error fetching data", error);
  }
};

// const rows = [
//   {
//     id: "1",
//     client_id: "INV-1234",
//     client_name: "Olivia Ryhe",
//     phone_number: "123-456-7890",
//     date: "Feb 3, 2023",
//     download_status: "Successful",
//   },
//   {
//     id: "2",
//     client_id: "INV-1233",
//     client_name: "Steve Hampton",
//     phone_number: "234-567-8901",
//     date: "Feb 3, 2023",
//     download_status: "Cut in between",
//   },
//   {
//     id: "3",
//     client_id: "INV-1232",
//     client_name: "Ciaran Murray",
//     phone_number: "345-678-9012",
//     date: "Feb 3, 2023",
//     download_status: "Unsuccessful",
//   },
//   // Add more rows as needed
// ];

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

function RowMenu() {
  return (
    <Dropdown>
      <MenuButton
        slots={{ root: IconButton }}
        slotProps={{ root: { variant: "plain", color: "neutral", size: "sm" } }}
      >
        <MoreHorizRoundedIcon />
      </MenuButton>
      <Menu size="sm" sx={{ minWidth: 140 }}>
        <MenuItem>Edit</MenuItem>
        <MenuItem>Rename</MenuItem>
        <MenuItem>Move</MenuItem>
        <Divider />
        <MenuItem color="danger">Delete</MenuItem>
      </Menu>
    </Dropdown>
  );
}

export default function OrderTable() {
  const [order, setOrder] = React.useState("desc");
  const [selected, setSelected] = React.useState([]);
  const [open, setOpen] = React.useState(false);
  const [rows, setRows] = React.useState([]);
  const [searchDate, setSearchDate] = React.useState("2024-07-17");

  React.useEffect(() => {
    fetchData(searchDate, setRows);
  }, [searchDate]);

  const handleSearch = (event) => {
    setSearchDate(event.target.value);
  };

  const renderFilters = () => (
    <FormControl size="sm">
      <FormLabel>Date</FormLabel>
      <Input
        size="sm"
        placeholder="YYYY-MM-DD"
        value={searchDate}
        onChange={handleSearch}
      />
    </FormControl>
  );
  return (
    <React.Fragment>
      <Sheet
        className="SearchAndFilters-mobile"
        sx={{
          display: { xs: "flex", sm: "none" },
          my: 1,
          gap: 1,
        }}
      >
        <Input
          size="sm"
          placeholder="Search"
          startDecorator={<SearchIcon />}
          sx={{ flexGrow: 1 }}
        />
        <IconButton
          size="sm"
          variant="outlined"
          color="neutral"
          onClick={() => setOpen(true)}
        >
          <FilterAltIcon />
        </IconButton>
        <Modal open={open} onClose={() => setOpen(false)}>
          <ModalDialog aria-labelledby="filter-modal" layout="fullscreen">
            <ModalClose />
            <Typography id="filter-modal" level="h2">
              Filters
            </Typography>
            <Divider sx={{ my: 2 }} />
            <Sheet sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {renderFilters()}
              <Button color="primary" onClick={() => setOpen(false)}>
                Submit
              </Button>
            </Sheet>
          </ModalDialog>
        </Modal>
      </Sheet>
      <Box
        className="SearchAndFilters-tabletUp"
        sx={{
          borderRadius: "sm",
          py: 2,
          display: { xs: "none", sm: "flex" },
          flexWrap: "wrap",
          gap: 1.5,
          "& > *": {
            minWidth: { xs: "120px", md: "160px" },
          },
        }}
      >
        <FormControl sx={{ flex: 1 }} size="sm">
          <FormLabel>Search for order</FormLabel>
          <Input
            size="sm"
            placeholder="Search"
            startDecorator={<SearchIcon />}
          />
        </FormControl>
        {renderFilters()}
      </Box>
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
                      event.target.checked ? rows.map((row) => row.id) : []
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
              <th style={{ width: 140, padding: "12px 6px" }}>Date</th>
              <th style={{ width: 200, padding: "12px 6px" }}>Call Status</th>
              <th style={{ width: 100, padding: "12px 6px" }}>Recordings</th>
            </tr>
          </thead>
          <tbody>
            {stableSort(rows, getComparator(order, "client_id")).map((row) => (
              <tr key={row.id}>
                <td style={{ textAlign: "center" }}>
                  <Checkbox
                    size="sm"
                    checked={selected.includes(row.id)}
                    onChange={(event) => {
                      setSelected((ids) =>
                        event.target.checked
                          ? [...ids, row.id]
                          : ids.filter((item) => item !== row.id)
                      );
                    }}
                    sx={{ verticalAlign: "text-bottom" }}
                    color={selected.includes(row.id) ? "primary" : undefined}
                  />
                </td>
                <td>{row.client_id}</td>
                <td>{row.client_name}</td>
                <td>{row.phone_number}</td>
                <td>{row.date}</td>
                <td>
                  <Chip
                    variant="soft"
                    size="sm"
                    startDecorator={
                      row.download_status === "successful" ? (
                        <CheckRoundedIcon />
                      ) : row.download_status === "busy" ? (
                        <AutorenewRoundedIcon />
                      ) : (
                        <BlockIcon />
                      )
                    }
                    color={
                      row.download_status === "successful"
                        ? "success"
                        : row.download_status === "busy"
                        ? "warning"
                        : "danger"
                    }
                  >
                    {row.download_status}
                  </Chip>
                </td>
                <td>
                  <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
                    <Link level="body-xs" component="button">
                      Download
                    </Link>
                    {/* <RowMenu />  */}
                  </Box>
                </td>
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
          <FormControl orientation="horizontal" size="sm">
            <FormLabel>Rows per page:</FormLabel>
            <Select
              size="sm"
              value={10}
              sx={{ ml: 1, mr: 0.5 }}
              slotProps={{ button: { sx: { lineHeight: 1 } } }}
            >
              <Option value={10}>10</Option>
              <Option value={25}>25</Option>
              <Option value={50}>50</Option>
            </Select>
          </FormControl>
          <Divider orientation="vertical" />
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
