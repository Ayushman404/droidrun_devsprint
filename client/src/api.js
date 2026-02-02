import axios from "axios";

const API = axios.create({ baseURL: "http://localhost:8000" });

export const getStatus = () => API.get("/status");
export const startSystem = () => API.post("/start");
export const stopSystem = () => API.post("/stop");
export const getApps = () => API.get("/apps");
export const updateAppRule = (pkg, data) => API.post(`/apps/${pkg}`, data);
export const updateConfig = (data) => API.post("/config", data);
export const getConfig = () => API.get("/config");
export const getAnalytics = () => API.get("/analytics");
export const getSchedule = () => API.get("/schedule");
export const addSchedule = (data) => API.post("/schedule", data);
export const deleteSchedule = (id) => API.delete(`/schedule/${id}`);
export const getAgentStatus = () => API.get("/agent/status");