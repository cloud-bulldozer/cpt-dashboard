import React from 'react';
import ReactDOM from 'react-dom';
import './index.css';
import './common/fonts.css'
import { Provider } from 'react-redux'

import App from './App';
import store from "./store/store"
import ChristmasCracker from './ChristmasCracker';


ReactDOM.render(
  <React.StrictMode>
      <Provider store={store}>
          <App />
          <ChristmasCracker />
      </Provider>
  </React.StrictMode>,
  document.getElementById('root')
);
