import { BASE_URL } from "./apiConstants";
import axios from "axios";

const axiosInstance = axios.create({
  baseURL: BASE_URL,
  responseType: "json",
});

export default axiosInstance;
