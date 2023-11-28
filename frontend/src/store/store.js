import {configureStore} from "@reduxjs/toolkit";
import {rootReducer} from "./reducers";
import {logger} from "redux-logger/src";


const store = configureStore({
    reducer:rootReducer,
    middleware: (getDefaultMiddleware) =>
        window.location.hostname === "localhost" ? getDefaultMiddleware().concat(logger):  getDefaultMiddleware()
});

export default store;
