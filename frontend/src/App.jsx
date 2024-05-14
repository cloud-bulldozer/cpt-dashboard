import "./App.less";

import * as APP_ROUTES from "./utils/routeConstants";

import { BrowserRouter, Route, Routes } from "react-router-dom";

import Home from "./components/templates/Home";
import MainLayout from "./containers/MainLayout";
import OCP from "./components/templates/OCP";
import { useDispatch } from "react-redux";
import { useEffect } from "react";

function App() {
  const dispatch = useDispatch();

  useEffect(() => {}, [dispatch]);
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route element={<MainLayout />}>
            <Route index element={<Home />} />
            <Route path={APP_ROUTES.HOME} element={<Home />} />
            <Route path={APP_ROUTES.OCP} element={<OCP />} />
            <Route path={APP_ROUTES.QUAY} element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
