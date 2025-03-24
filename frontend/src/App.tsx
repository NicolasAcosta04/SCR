import { useState } from "react";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router";
import Home from "./pages/Home";

const App = () => {
  const [loggedIn, setLoggedIn] = useState(false); // add better authentication check

  const toggleRoute = () => {
    setLoggedIn((prev) => !prev);
  };

  return (
    <>
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              !loggedIn ? (
                // <Login />
                <button onClick={toggleRoute}>Toggle</button>
              ) : (
                <Navigate replace to={"/home"} />
              )
            }
          />
          <Route path="/home" element={<Home />} />
          <Route path="/profile" element={<div>Profile</div>} />
          <Route path="/settings" element={<div>Settings</div>} />
        </Routes>
      </Router>
    </>
  );
};

export default App;
