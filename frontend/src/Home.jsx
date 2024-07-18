import * as React from "react";
import Button from "@mui/joy/Button";
import SvgIcon from "@mui/joy/SvgIcon";
import { styled } from "@mui/joy";
import { useState } from "react";
import axios from "axios";
import { CircularProgress, Typography, Box } from "@mui/material";
import { useNavigate } from "react-router-dom";

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const VisuallyHiddenInput = styled("input")`
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  bottom: 0;
  left: 0;
  white-space: nowrap;
  width: 1px;
`;

const CenteredContainer = styled("form")`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 100vw;
  height: 100vh; /* Adjust height as needed */
`;

export default function InputFileUpload() {
  const [file, setFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const navigate = useNavigate();

  const handleChange = (event) => {
    setFile(event.target.files[0]);
  };

  const handleUpload = async (event) => {
    event.preventDefault();
    setIsProcessing(true);
    const formData = new FormData();
    formData.append("file", file);
    sleep(4000);
    try {
      const response = await axios.post(
        "https://trading-call.onrender.com/upload", // Replace with your backend endpoint
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );

      console.log(response.data); // Handle response from server
      if (response.status === 200) {
        navigate("/calls"); // Navigate to calls if upload is successful
      }
    } catch (error) {
      // alert("There has been error, please try again");
      console.error("Error uploading file:", error);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <CenteredContainer>
      <Button
        style={{ position: "absolute", top: "10px", right: "10px" }}
        variant="outlined"
        onClick={() => navigate("/calls")}
      >
        Go to calls
      </Button>
      <Button
        style={{ width: "15%" }}
        component="label"
        role={undefined}
        tabIndex={-1}
        variant="outlined"
        color="neutral"
        startDecorator={
          <SvgIcon>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 16.5V9.75m0 0l3 3m-3-3l-3 3M6.75 19.5a4.5 4.5 0 01-1.41-8.775 5.25 5.25 0 0110.233-2.33 3 3 0 013.758 3.848A3.752 3.752 0 0118 19.5H6.75z"
              />
            </svg>
          </SvgIcon>
        }
      >
        Upload a file
        <VisuallyHiddenInput type="file" onChange={handleChange} />
      </Button>
      {file && (
        <Typography variant="body1" style={{ marginTop: "10px" }}>
          File: {file.name}
        </Typography>
      )}
      <Button
        style={{ width: "15%", margin: "15px" }}
        type="submit"
        onClick={handleUpload}
      >
        Submit
      </Button>
      {isProcessing && (
        <Box display="flex" alignItems="center">
          <CircularProgress />
          <Typography variant="body1" style={{ marginLeft: "10px" }}>
            Processing...
          </Typography>
        </Box>
      )}
    </CenteredContainer>
  );
}
