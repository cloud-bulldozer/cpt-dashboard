import {configureStore} from "@reduxjs/toolkit";
import {rootReducer} from "./reducers";
import {logger} from "redux-logger/src";


const store = configureStore({reducer:rootReducer, middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(logger)});

export default store;
