import axios from "axios";

export const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";
export const API_TIMEOUT_MS = 15000;

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT_MS,
  headers: {
    "Content-Type": "application/json",
  },
});

function extractErrorMessage(error) {
  if (error.code === "ECONNABORTED") {
    return "Request timed out. Please try again.";
  }
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  if (error.message) {
    return error.message;
  }
  return "The analysis service is currently unavailable.";
}

export async function predictNews(payload) {
  const response = await api.request({
    method: "post",
    url: "/api/predict",
    data: payload,
  });
  return response.data;
}

export async function fetchBackendHealth() {
  const response = await api.request({
    method: "get",
    url: "/api/health",
  });
  return response.data;
}

export async function fetchModelStats() {
  const response = await api.request({
    method: "get",
    url: "/api/stats",
  });
  return response.data;
}

export { extractErrorMessage };
