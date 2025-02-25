import "./App.less";

import * as APP_ROUTES from "./utils/routeConstants";

import { BrowserRouter, Route, Routes } from "react-router-dom";

import Home from "./components/templates/Home";
import MainLayout from "./containers/MainLayout";
import OCP from "./components/templates/OCP";
import OLS from "./components/templates/OLS";
import Quay from "./components/templates/Quay";
import Telco from "./components/templates/Telco";
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
            <Route path={APP_ROUTES.TELCO} element={<Telco />} />
            <Route path={APP_ROUTES.OLS} element={<OLS />} />
            <Route path={APP_ROUTES.QUAY} element={<Quay />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
