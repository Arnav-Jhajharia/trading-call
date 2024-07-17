import React from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import Home from "./Home";
import Orders from "./Order";

function App() {
  return (
    <Router>
      <div className="App">
        {/* <Switch> */}
        <Routes>
          <Route path="/" exact element={<Home />} />
          <Route path="/order" exact element={<Orders />} />
        </Routes>
        {/* </Switch> */}
      </div>
    </Router>
  );
}

export default App;
